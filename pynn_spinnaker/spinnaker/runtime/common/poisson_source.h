#pragma once

// Common includes
#include "fixed_point_number.h"
#include "log.h"
#include "spinnaker.h"
#include "spike_recording.h"
#include "utils.h"
#include "random/non_uniform.h"

// Namespaces
using namespace Common::FixedPointNumber;
using namespace Common::Random;
using namespace Common;
using namespace Common::Utils;

//-----------------------------------------------------------------------------
// Common::PoissonSource
//-----------------------------------------------------------------------------
namespace Common
{
template <typename R>
class PoissonSource
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  // Poisson source doesn't use any DMA tags
  static const uint DMATagMax = 0;

  PoissonSource() : m_NumSlow(0), m_SlowImmutableState(NULL), m_SlowTimeToSpike(NULL), m_NumFast(0), m_FastImmutableState(NULL)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "PoissonSource::ReadSDRAMData");

    // Read RNG seed
    uint32_t seed[R::StateSize];
    LOG_PRINT(LOG_LEVEL_TRACE, "\tSeed:");
    for(unsigned int s = 0; s < R::StateSize; s++)
    {
      seed[s] = *region++;
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\t%u", seed[s]);
    }
    m_RNG.SetState(seed);

    // Read number of slow spikes sources, followed by array of structs
    m_NumSlow = (unsigned int)*region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\t%u slow spike sources", m_NumSlow);
    if(!AllocateCopyStructArray(m_NumSlow, region, m_SlowImmutableState))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate slow spike source immutable state array");
      return false;
    }

    // If there are any slow spike sources
    if(m_NumSlow > 0)
    {
      // Allocate array
      m_SlowTimeToSpike = (S1615*)spin1_malloc(sizeof(S1615) * m_NumSlow);
      if(m_SlowTimeToSpike == NULL)
      {
        LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate slow spike source time to spikearray");
        return false;
      }

      // Calculate initial time-to-spike for each slow source
      for(unsigned int s = 0; s < m_NumSlow; s++)
      {
        m_SlowTimeToSpike[s] = m_SlowImmutableState[s].CalculateTTS(m_RNG);

  #if LOG_LEVEL <= LOG_LEVEL_TRACE
        io_printf(IO_BUF, "Slow spike source %u:\n", s);
        m_SlowImmutableState[s].Print(IO_BUF);
        io_printf(IO_BUF, "\tTTS            = %k\n", m_SlowTimeToSpike[s]);
  #endif
      }
    }

    // Read number of fast spikes sources, followed by array of structs
    m_NumFast = (unsigned int)*region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\t%u fast spike sources", m_NumFast);
    if(!AllocateCopyStructArray(m_NumFast, region, m_FastImmutableState))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate fast spike source immutable state array");
      return false;
    }

  #if LOG_LEVEL <= LOG_LEVEL_TRACE
    for(unsigned int s = 0; s < m_NumFast; s++)
    {
      io_printf(IO_BUF, "Fast spike source %u:\n", s);
      m_FastImmutableState[s].Print(IO_BUF);
    }
  #endif

    return true;
  }

  bool DMATransferDone(uint)
  {
    return false;
  }

  template<typename E>
  void Update(uint tick, E emitSpikeFunction, SpikeRecording &spikeRecording,
              unsigned int)
  {
    auto *tts = m_SlowTimeToSpike;
    const uint16_t *immutableStateIndex = m_ImmutableStateIndices;
    for(unsigned int n = 0; n < g_AppWords[AppWordNumNeurons]; n++)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tSimulating neuron %u", n);

      // Get synaptic input
      auto &synMutable = *synapseMutableState++;
      const auto &synImmutable = g_SynapseImmutableState[*synapseImmutableStateIndex++];
      S1615 excInput = Synapse::GetExcInput(synMutable, synImmutable);
      S1615 inhInput = Synapse::GetInhInput(synMutable, synImmutable);
    }
    // Loop through slow source
    auto *slowTimeToSpike = m_SlowTimeToSpike;
    const auto *slowImmutableState = m_SlowImmutableState;
    for(unsigned int s = 0; s < m_NumSlow; s++)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tSimulating slow spike source %u", s);

      auto &tts = *slowTimeToSpike++;
      const auto &immutable = *slowImmutableState++;

      // If this source should be active
      bool spiked = false;
      if(immutable.IsActive(tick))
      {
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\tTime-to-spike:%k ticks", tts);

        // If it's time to spike
        if(tts <= 0)
        {
          // Set spiked flag
          spiked = true;

          // Emit a spike
          LOG_PRINT(LOG_LEVEL_TRACE, "\t\tEmitting spike");
          emitSpikeFunction(immutable.GetNeuronID());

          // Update time-to-spike
          S1615 nextTTS = immutable.CalculateTTS(m_RNG);
          LOG_PRINT(LOG_LEVEL_TRACE, "\t\tNext time-to-spike:%k ticks", nextTTS);
          tts += nextTTS;
        }

        // Subtract one
        tts -= S1615One;
      }

      // Record spike
      spikeRecording.RecordSpike(immutable.GetNeuronID(), spiked);
    }

    // Loop through fast source
    const auto *fastImmutableState = m_FastImmutableState;
    for(unsigned int f = 0; f < m_NumFast; f++)
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\tSimulating fast spike source %u", f);

      const auto &immutable = *fastImmutableState++;

      // If this source should be active
      bool spiked = false;
      if(immutable.IsActive(tick))
      {
        // Get number of spikes to emit this timestep
        unsigned int numSpikes = immutable.GetNumSpikes(m_RNG);
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\tEmitting %u spikes", numSpikes);

        // Determine if this means it spiked
        spiked = (numSpikes > 0);

        // Emit spikes
        for(unsigned int s = 0; s < numSpikes; s++)
        {
          emitSpikeFunction(immutable.GetNeuronID());
        }
      }

      // Record spike
      spikeRecording.RecordSpike(immutable.GetNeuronID(), spiked);
    }

  }

private:
  //-----------------------------------------------------------------------------
  // Immutable
  //-----------------------------------------------------------------------------
  class Immutable
  {
  public:
    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    void Print(char *stream) const
    {
      io_printf(stream, "\tStartTick      = %u\n", m_StartTick);
      io_printf(stream, "\tEndTick        = %u\n", m_EndTick);
      if(m_IsSlow)
      {
        io_printf(stream, "\tMeanISI        = %k\n", m_Data.m_MeanISI);
      }
      else
      {
        io_printf(stream, "\tExpMinusLambda = %k\n", (S1615)(m_Data.m_ExpMinusLambda >> 17));
      }
    }

    bool Update(S1615 &slowTimeToSpike, R &rng, E emitSpikeFunction)
    {
      // If spike source is active, return result of correct update function
      if((tick >= m_StartTick) && (tick < m_EndTick))
      {
        if(m_IsSlow)
        {
          return UpdateSlow(slowTimeToSpike, rng, emitSpikeFunction);
        }
        else
        {
          return UpdateFast(rng, emitSpikeFunction);
        }
      }
      // Otherwise, return false
      else
      {
        return false;
      }
    }

  private:
    //-----------------------------------------------------------------------------
    // Unions
    //-----------------------------------------------------------------------------
    union TypeSpecificData;
    {Immutable
      S1615 m_MeanISI;
      U032 m_ExpMinusLambda;
    };

    //-----------------------------------------------------------------------------
    // Private methods
    //-----------------------------------------------------------------------------
    bool UpdateSlow(S1615 &tts, R &rng, E emitSpikeFunction)
    {
      // If it's time to spike
      const bool spiked = (tts <= 0);
      if(spiked)
      {
        // Update time-to-spike
        S1615 nextTTSImmutable = MulS1615(m_Data.m_MeanISI, NonUniform::ExponentialDistVariate(rng));
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\tNext time-to-spike:%k ticks", nextTTS);
        tts += nextTTS;
      }

      // Subtract one
      tts -= S1615One;

      // Return whether spikes have been emitted
      return spiked;
    }

    bool UpdateFast(R &rng, E emitSpikeFunction)
    {
      // Get number of spikes to emit this timestep
      unsigned int numSpikes = NonUniform::PoissonDistVariate(rng, m_Data.m_ExpMinusLambda);
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tEmitting %u spikes", numSpikes);

      // Emit spikes
      for(unsigned int s = 0; s < numSpikes; s++)
      {
        emitSpikeFunction();
      }

      // Return true if any spikes have been emitted
      return (numSpikes > 0);
    }

    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    bool m_IsSlow;
    uint32_t m_StartTick;
    uint32_t m_EndTick;
    TypeSpecificData m_Data;
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  unsigned int m_NumSpikeSources;
  Immutable *m_ImmutableState;
  uint16_t *m_ImmutableStateIndices;
  S1615 *m_SlowTimeToSpike;

  R m_RNG;
};
} // Common