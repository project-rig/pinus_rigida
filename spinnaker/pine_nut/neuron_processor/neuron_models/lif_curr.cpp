#include "lif_curr.h"

// Sark includes
extern "C"
{
  #include <sark.h>
}

//-----------------------------------------------------------------------------
// LIFCurr
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
namespace NeuronModels
{
void LIFCurr::Print(char *stream, const MutableState &mutableState, const ImmutableState &immutableState)
{
  io_printf(stream, "Mutable state:\n");
  io_printf(stream, "V_Membrane       = %11.4k [mV]\n", mutableState.m_V_Membrane);
  io_printf(stream, "RefractoryTimer  = %u [timesteps]\n", mutableState.m_RefractoryTimer);

  io_printf(stream, "Immutable state:\n");
  io_printf(stream, "V_Threshold      = %11.4k [mV]\n", immutableState.m_V_Threshold);
  io_printf(stream, "V_Reset          = %11.4k [mV]\n", immutableState.m_V_Reset);
  io_printf(stream, "V_Rest           = %11.4k [mV]\n", immutableState.m_V_Rest);
  io_printf(stream, "I_Offset         = %11.4k [mV]\n", immutableState.m_I_Offset);
  io_printf(stream, "R_Membrane       = %11.4k [MegaOhm]\n", immutableState.m_R_Membrane);
  io_printf(stream, "ExpTC            = %11.4k\n", immutableState.m_ExpTC);
  io_printf(stream, "T_Refractory     = %u [timesteps]\n", immutableState.m_T_Refractory);
}
};  // namespace NeuronModels
};  // namespace NeuronProcessor