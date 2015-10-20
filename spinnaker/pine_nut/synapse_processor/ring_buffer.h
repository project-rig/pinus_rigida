#pragma once

//-----------------------------------------------------------------------------
// SynapseProcessor::RingBufferBase
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
template<typename T, typename S>
class RingBufferBase
{
public:
  typedef T Type;

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const unsigned int OutputBufferSize = (1 << S::NumIndexBits);
  static const unsigned int Size = (1 << (S::NumDelayBits + S::NumIndexBits));

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void AddWeight(unsigned int tick, unsigned int index,
    Type weight)
  {
    // Calculate ring buffer offset
    uint32_t offset = OffsetTypeIndex(tick, index);

    // Add value to ring-buffer
    m_Data[offset] += weight;
  }

  const Type *GetOutputBuffer(uint32_t tick) const
  {
    // Calculate ring-buffer offset for this time
    unsigned int offset = OffsetTime(tick);

    return &m_Data[offset];
  }

private:
  //-----------------------------------------------------------------------------
  // Static methods
  //-----------------------------------------------------------------------------
  static unsigned int OffsetTime(unsigned int tick)
  {
    return ((tick & S::DelayMask) << S::NumIndexBits);
  }

  static unsigned int OffsetTypeIndex(unsigned int tick, unsigned int index)
  {
    return OffsetTime(tick) | index;
  }

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  Type m_Data[Size];
};
} // SynapseProcessor


//-----------------------------------------------------------------------------
// Global functions
//-----------------------------------------------------------------------------
//bool ring_buffer_init();
//void ring_buffer_clear_output_buffer(uint32_t tick);

//#endif  // RING_BUFFER_H