#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/bit_field.h"
#include "../common/fixed_point_number.h"
#include "../common/log.h"
#include "../common/spinnaker.h"
#include "../common/utils.h"

// Namespaces
using namespace Common;
using namespace Common::FixedPointNumber;
using namespace Common::Utils;

//-----------------------------------------------------------------------------
// NeuronProcessor::AnalogueRecording
//-----------------------------------------------------------------------------
namespace NeuronProcessor
{
class AnalogueRecording
{
public:
  AnalogueRecording() : m_IndicesToRecord(NULL), m_RecordSDRAM(NULL)  {}

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool ReadSDRAMData(uint32_t *region, uint32_t, unsigned int numNeurons)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tAnalogueRecording::ReadSDRAMData");

     // Calculate number of words that are required to build a bitfield for ALL neurons
    unsigned int numWords = BitField::GetWordSize(numNeurons);
    LOG_PRINT(LOG_LEVEL_INFO, "\t\tNum words per population:%u", numWords);

    // Copy indices to record
    if(!AllocateCopyStructArray(numWords, region, m_IndicesToRecord))
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Unable to allocate indices to record array");
      return false;
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    BitField::PrintBits(IO_BUF, m_IndicesToRecord, numWords);
    io_printf(IO_BUF, "\n");
#endif

    // Cache pointer of subsequent data
    m_RecordSDRAM = (S1615*)region;
    LOG_PRINT(LOG_LEVEL_INFO, "\t\tRecording starting at %08x", m_RecordSDRAM);

    return true;
  }

  void RecordValue(unsigned int neuron, S1615 value)
  {
    // If we should record this channel for this neuron in this channel
    if(BitField::TestBit(m_IndicesToRecord, neuron))
    {
      LOG_PRINT(LOG_LEVEL_TRACE, "\t\tRecording neuron:%u, value:%k",
                neuron,  value);

      // Write value to SDRAM
      *m_RecordSDRAM++ = value;
    }
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  // Bit field specifying which neurons to record
  uint32_t *m_IndicesToRecord;

  // Pointer to SDRAM to write next value to
  S1615 *m_RecordSDRAM;
};
}