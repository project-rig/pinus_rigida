#include "cond.h"

// Common includes
#include "../../common/spinnaker.h"

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronInputModels::Curr
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronInputModels
{
void Cond::Print(char *stream, const MutableState &, const ImmutableState &immutableState)
{
  io_printf(stream, "Conductance input\n");
  io_printf(stream, "\tImmutable state:\n");
  io_printf(stream, "\t\tV_RevExc         = %11.4k [mV]\n", immutableState.m_V_RevExc);
  io_printf(stream, "\t\tV_RevInh         = %11.4k [mV]\n", immutableState.m_V_RevInh);
}
};  // namespace NeuronInputModels
};  // namespace NeuronProcessor