#include "exp.h"

#include "../../common/spinnaker.h"

//-----------------------------------------------------------------------------
// NeuronProcessor::SynapseModels::Exp
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace SynapseModels
{
void Exp::Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState)
{
  io_printf(stream, "\tMutable state:\n");
  io_printf(stream, "\t\tm_ISynExc        = %11.4k [nA]\n", mutableState.m_ISynExc);
  io_printf(stream, "\t\tm_ISynInh        = %11.4k [nA]\n", mutableState.m_ISynInh);

  io_printf(stream, "\tImmutable state:\n");
  io_printf(stream, "\t\tExpTauSynExc      = %11.4k\n", immutableState.m_ExpTauSynExc);
  io_printf(stream, "\t\tInitE             = %11.4k [nA]\n", immutableState.m_InitE);
  io_printf(stream, "\t\tExpTauSynInh      = %11.4k\n", immutableState.m_ExpTauSynInh);
  io_printf(stream, "\t\tInitI             = %11.4k [nA]\n", immutableState.m_InitI);
}
};  // namespace NeuronModels
};  // namespace NeuronProcessor