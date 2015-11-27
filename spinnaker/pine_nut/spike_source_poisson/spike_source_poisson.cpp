#include "spike_source_poisson.h"

// Standard includes
#include <climits>

// Common includes
#include "../common/config.h"
#include "../common/fixed_point_number.h"
#include "../common/random/mars_kiss64.h"
#include "../common/random/non_uniform.h"
#include "../common/log.h"
#include "../common/spike_recording.h"
#include "../common/spinnaker.h"
#include "../common/utils.h"

// Namespaces
using namespace Common::FixedPointNumber;
using namespace Common::Random;
using namespace Common;
using namespace Common::Utils;
using namespace SpikeSourcePoisson;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{
//-----------------------------------------------------------------------------
// ImmutableBase
//-----------------------------------------------------------------------------
class ImmutableBase
{
public:
  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool IsActive(unsigned int tick) const
  {
    return ((tick >= m_StartTick) && (tick < m_EndTick));
  }

  uint32_t GetNeuronID() const { return m_NeuronID; }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_NeuronID;
  uint32_t m_StartTick;
  uint32_t m_EndTick;
};

//-----------------------------------------------------------------------------
// SlowImmutable
//-----------------------------------------------------------------------------
//! data structure for spikes which have multiple timer tick between firings
//! this is separated from spikes which fire at least once every timer tick as
//! there are separate algorithms for each type.
class SlowImmutable : public ImmutableBase
{
public:
  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  template<typename R>
  S1615 CalculateTTS(R rng) const
  {
    return MulS1615(m_MeanISI, NonUniform::ExponentialDistVariate(rng));
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  S1615 m_MeanISI;
};

//-----------------------------------------------------------------------------
// FastImmutable
//-----------------------------------------------------------------------------
//! data structure for spikes which have at least one spike fired per timer tick
//! this is separated from spikes which have multiple timer ticks between firings
//! as there are separate algorithms for each type.
class FastImmutable : public ImmutableBase
{
public:
  //-----------------------------------------------------------------------------
  // GetNumSpikes
  //-----------------------------------------------------------------------------
  template<typename R>
  unsigned int GetNumSpikes(R rng) const
  {
    return NonUniform::PoissonDistVariate(rng, m_ExpMinusLambda);
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  U032 m_ExpMinusLambda;
};

//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Common::Config g_Config;
uint32_t g_AppWords[AppWordMax];

SpikeRecording g_SpikeRecording;
MarsKiss64 g_RNG;

unsigned int g_NumSlow = 0;
SlowImmutable *g_SlowImmutableState = NULL;
S1615 *g_SlowTimeToSpike = NULL;

unsigned int g_NumFast = 0;
FastImmutable *g_FastImmutableState = NULL;

//----------------------------------------------------------------------------
// Functions
//----------------------------------------------------------------------------
bool ReadPoissonSourceRegion(uint32_t *region, uint32_t)
{
  LOG_PRINT(LOG_LEVEL_INFO, "ReadPoissonSourceRegion");

  // Read RNG seed
  uint32_t seed[MarsKiss64::SeedSize];
  LOG_PRINT(LOG_LEVEL_TRACE, "\tSeed:");
  for(unsigned int s = 0; s < MarsKiss64::SeedSize; s++)
  {
    seed[s] = *region++;
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u", seed[s]);
  }
  g_RNG.SetSeed(seed);

  // Read number of slow spikes sources, followed by array of structs
  g_NumSlow = (unsigned int)*region++;
  LOG_PRINT(LOG_LEVEL_INFO, "\t%u slow spike sources", g_NumSlow);
  if(!AllocateCopyStructArray(g_NumSlow, region, g_SlowImmutableState))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate slow spike source immutable state array");
    return false;
  }

  // Read number of fast spikes sources, followed by array of structs
  g_NumFast = (unsigned int)*region++;
  LOG_PRINT(LOG_LEVEL_TRACE, "\tNeuron immutable state");
  if(!AllocateCopyStructArray(g_NumFast, region, g_FastImmutableState))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate fast spike source immutable state array");
    return false;
  }
  
  // If there are any slow spike sources
  if(g_NumSlow > 0)
  {
    // Allocate array
    g_SlowTimeToSpike = (S1615*)spin1_malloc(sizeof(S1615) * g_NumSlow);
    if(g_SlowTimeToSpike == NULL)
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate slow spike source time to spikearray");
      return false;
    }

    // Calculate initial time-to-spike for each slow source
    for(unsigned int i = 0; i < g_NumSlow; i++)
    {
      g_SlowTimeToSpike[i] = g_SlowImmutableState[i].CalculateTTS(g_RNG);
    }
  }
  
  return true;
}
//-----------------------------------------------------------------------------
bool ReadSDRAMData(uint32_t *baseAddress, uint32_t flags)
{
  // Verify data header
  if(!g_Config.VerifyHeader(baseAddress, flags))
  {
    return false;
  }

  // Read system region
  if(!g_Config.ReadSystemRegion(
    Common::Config::GetRegionStart(baseAddress, RegionSystem),
    flags, AppWordMax, g_AppWords))
  {
    return false;
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tkey=%08x, num spike sources=%u",
      g_AppWords[AppWordKey], g_AppWords[AppWordNumSpikeSources]);
  }
  
  // Read poisson source region
  if(!ReadPoissonSourceRegion(
    Common::Config::GetRegionStart(baseAddress, RegionPoissonSource), flags))
  {
    return false;
  }

  // Read spike recording region
  if(!g_SpikeRecording.ReadSDRAMData(
    Common::Config::GetRegionStart(baseAddress, RegionSpikeRecording), flags,
    g_AppWords[AppWordNumSpikeSources]))
  {
    return false;
  }

  return true;
}
//-----------------------------------------------------------------------------
void EmitSpike(unsigned int n)
{
  // Send spike
    uint32_t key = g_AppWords[AppWordKey] | n;
    while(!spin1_send_mc_packet(key, 0, NO_PAYLOAD))
    {
      spin1_delay_us(1);
    }
}

//-----------------------------------------------------------------------------
// Event handler functions
//-----------------------------------------------------------------------------
static void TimerTick(uint tick, uint)
{
  // Subtract 1 from tick as they start at 1
  tick--;

  // If a fixed number of simulation ticks are specified and these have passed
  if(g_Config.GetSimulationTicks() != UINT32_MAX
    && tick >= g_Config.GetSimulationTicks())
  {
    LOG_PRINT(LOG_LEVEL_INFO, "Simulation complete");

    // Finalise any recordings that are in progress, writing
    // back the final amounts of samples recorded to SDRAM
    //recording_finalise();
    spin1_exit(0);
  }
  // Otherwise
  else
  {
    // Loop through slow source
    auto *slowTimeToSpike = g_SlowTimeToSpike;
    const auto *slowImmutableState = g_SlowImmutableState;
    for(unsigned int s = 0; s < g_NumSlow; s++)
    {
      auto &tts = *slowTimeToSpike++;
      const auto &immutable = *slowImmutableState++;

      // If this source should be active
      bool spiked = false;
      if(immutable.IsActive(tick))
      {
        // If it's time to spike
        if(tts <= 0)
        {
          // Set spiked flag
          spiked = true;

          // Emit a spike
          LOG_PRINT(LOG_LEVEL_TRACE, "\t\tEmitting spike");
          EmitSpike(immutable.GetNeuronID());

          // Update time-to-spike
          tts += immutable.CalculateTTS(g_RNG);
        }

        // Subtract one
        tts -= S1615One;
      }

      // Record spike
      g_SpikeRecording.RecordSpike(immutable.GetNeuronID(), spiked);
    }

    // Loop through fast source
    const auto *fastImmutableState = g_FastImmutableState;
    for(unsigned int f = 0; f < g_NumFast; f++)
    {
      const auto &immutable = *fastImmutableState++;

      // If this source should be active
      bool spiked = false;
      if(immutable.IsActive(tick))
      {
        // Get number of spikes to emit this timestep
        unsigned int numSpikes = immutable.GetNumSpikes(g_RNG);

        // Determine if this means it spiked
        spiked = (numSpikes > 0);

        // Emit spikes
        for(unsigned int s = 0; s < numSpikes; s++)
        {
          EmitSpike(immutable.GetNeuronID());
        }
      }

      // Record spike
      g_SpikeRecording.RecordSpike(immutable.GetNeuronID(), spiked);
    }
  }
}
} // Anonymous namespace

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void c_main()
{
  // Get this core's base address using alloc tag
  uint32_t *baseAddress = Common::Config::GetBaseAddressAllocTag();
  
  // If reading SDRAM data fails
  if(!ReadSDRAMData(baseAddress, 0))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data");
    return;
  }
  
  // Set timer tick (in microseconds) in both timer and 
  spin1_set_timer_tick(g_Config.GetTimerPeriod());
  
  // Register callbacks
  spin1_callback_on(TIMER_TICK,         TimerTick,        2);
  
  // Start simulation
  spin1_start(SYNC_WAIT);
}