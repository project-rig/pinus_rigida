#pragma once

//----------------------------------------------------------------------------
// Common::RowOffsetLength
//----------------------------------------------------------------------------
namespace Common
{
template<unsigned int S>
class RowOffsetLength
{
public:
  RowOffsetLength(){}
  RowOffsetLength(uint32_t wordOffset) : m_WordOffset(wordOffset){}

  //--------------------------------------------------------------------------
  // Public API
  //--------------------------------------------------------------------------
  uint32_t GetNumSynapses() const
  {
    return (m_WordOffset & RowSynapsesMask) + 1;
  }

  uint32_t GetWordOffset() const
  {
    return (m_WordOffset >> S);
  }

private:
  //--------------------------------------------------------------------------
  // Constants
  //--------------------------------------------------------------------------
  static const uint32_t RowSynapsesMask = (1 << S) - 1;

  //--------------------------------------------------------------------------
  // Members
  //--------------------------------------------------------------------------
  uint32_t m_WordOffset;
};
} // Common