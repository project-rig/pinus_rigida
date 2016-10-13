#include "curr.h"

// Common includes
#include "../../common/spinnaker.h"

//-----------------------------------------------------------------------------
// NeuronProcessor::NeuronInputModels::Curr
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronInputModels
{
void Curr::Print(char *stream, const MutableState &, const ImmutableState &)
{
  io_printf(stream, "Current input\n");
}
};  // namespace NeuronInputModels
};  // namespace NeuronProcessor