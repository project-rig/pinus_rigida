#include "constant.h"

// Common includes
#include "../../common/spinnaker.h"

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronThresholdModels::Curr
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronThresholdModels
{
void Constant::Print(char *stream, const MutableState &, const ImmutableState &immutableState)
{
  io_printf(stream, "Constant threshold\n");
  io_printf(stream, "\tImmutable state:\n");
  io_printf(stream, "\t\tV_Threshold      = %11.4k [mV]\n", immutableState.m_V_Threshold);
}
};  // namespace NeuronThresholdModels
};  // namespace NeuronProcessor