#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../../../common/exp_decay_lut.h"
#include "../../../common/fixed_point_number.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// SynapseProcessor::Plasticity::TimingDependences::Pair
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
namespace Plasticity
{
namespace TimingDependences
{
template<unsigned int TauPlusLUTNumEntries, unsigned int TauPlusLUTShift,
         unsigned int TauMinusLUTNumEntries, unsigned int TauMinusLUTShift>
class Pair
{
public:
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef uint16_t PostTrace;
  typedef uint16_t PreTrace;

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  PostTrace UpdatePostTrace(uint32_t time, uint32_t lastTime, PostTrace lastTrace) const
  {
    // Get time since last spike
    uint32_t deltaTime = time - lastTime;

    // Decay previous trace
    int32_t newTrace = MulS511(lastTrace, m_TauMinusLUT.Get(deltaTime));

    // Add energy caused by new spike to trace
    newTrace += S511One;

    //log_debug("\tdelta_time=%d, o1=%d\n", deltaTime, newTrace);

    // Return new trace_value
    return (PostTrace)newTrace;
  }

  PreTrace UpdatePreTrace(uint32_t time, uint32_t last_time, PreTrace lastTrace, bool flush) const
  {
    // Get time since last spike
    uint32_t deltaTime = time - lastTime;

    // Decay previous trace
    int32_t newTrace = MulS511(lastTrace, m_TauPlusLUT.Get(deltaTime));

    // If this isn't a flush, add energy caused by new spike to trace
    if(!flush)
    {
      newTrace += S511One;
    }

    //log_debug("\tdelta_time=%d, o1=%d\n", deltaTime, newTrace);

    // Return new trace_value
    return (PreTrace)newTrace;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  Common::ExpDecayLUT<TauPlusLUTNumEntries, TauPlusLUTShift> m_TauPlusLUT;
  Common::ExpDecayLUT<TauMinusLUTNumEntries, TauMinusLUTShift> m_TauMinusLUT;
};
} // TimingDependences
} // Plasticity
} // SynapseProcessor