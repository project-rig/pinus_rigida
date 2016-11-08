#include "matrix_generator.h"

// Standard includes
#include <algorithm>

// Common includes
#include "../common/log.h"
#include "../common/row_offset_length.h"

// Connection builder includes
#include "connector_generator.h"
#include "param_generator.h"

// **YUCK** standard algorithms tend to rely on memcpy under the hood.
// This wraps the SpiNNaker memcpy routine in a suitable form
// it probably belongs somewhere else though
void* memcpy(void* dest, const void* src, std::size_t count)
{
  spin1_memcpy(dest, src, count);
  return dest;
}


//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Base
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Base::Base(uint32_t *&region)
{
  m_SignedWeight = *region++;
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Base::TraceUInt(uint32_t (&values)[1024],
                                                         unsigned int number) const
{
#if LOG_LEVEL <= LOG_LEVEL_TRACE
  for(unsigned int i = 0; i < number; i++)
  {
    io_printf(IO_BUF, "%u,", values[i]);
  }
  io_printf(IO_BUF, "\n");
#endif
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::MatrixGenerator::Base::TraceInt(int32_t (&values)[1024],
                                                        unsigned int number) const
{
#if LOG_LEVEL <= LOG_LEVEL_TRACE
  for(unsigned int i = 0; i < number; i++)
  {
    io_printf(IO_BUF, "%u,", values[i]);
  }
  io_printf(IO_BUF, "\n");
#endif
}
//-----------------------------------------------------------------------------
unsigned int ConnectionBuilder::MatrixGenerator::Base::GenerateRow(unsigned int row,
  unsigned int weightFixedPoint, unsigned int numPostNeurons,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  uint32_t (&indices)[1024], int32_t (&delays)[1024], int32_t (&weights)[1024],
  MarsKiss64 &rng) const
{
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating indices");
  const unsigned int numIndices = connectorGenerator->Generate(row, numPostNeurons,
                                                               rng, indices);
  TraceUInt(indices, numIndices);
  
  // Generate delays for each index
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating delays");
  delayGenerator->Generate(numIndices, 0, rng, delays);
  TraceInt(delays, numIndices);

  // Generate weights for each index
  LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tGenerating weights");
  weightGenerator->Generate(numIndices, weightFixedPoint, rng, weights);
  TraceInt(weights, numIndices);

  // Return row length
  return numIndices;
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Static
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Static::Static(uint32_t *&region) : Base(region)
{
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tStatic synaptic matrix: %u signed weights",
    IsSignedWeight());
}
//-----------------------------------------------------------------------------
bool ConnectionBuilder::MatrixGenerator::Static::Generate(
  uint32_t *synapticMatrixBaseAddress, uint32_t *matrixAddress,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint,
  unsigned int numPostNeurons, unsigned int sizeWords, unsigned int numRows,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  MarsKiss64 &rng) const
{
  typedef Common::RowOffsetLength<10> RowOffsetLength;

  // End address of matrix
  uint32_t *endAddress = matrixAddress + sizeWords;

  // Ragged section of matrix begins at matrix address
  uint32_t *raggedMatrixAddress = matrixAddress;

  // Delay extension section of matrix begins after padded ragged matrix
  uint32_t *delayMatrixAddress = matrixAddress + ((3 + maxRowSynapses) * numRows);

  // Loop through rows
  unsigned int numSynapses = 0;
  for(unsigned int i = 0; i < numRows; i++)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tRow %u", i);

    // Generate indices, weights and delays for row
    uint32_t indices[1024];
    int32_t delays[1024];
    int32_t weights[1024];
    const unsigned int numIndices = GenerateRow(i,
      weightFixedPoint, numPostNeurons, connectorGenerator, delayGenerator,
      weightGenerator, indices, delays, weights, rng);

    // Update total number of synapses
    numSynapses += numIndices;

    // Generate indices so as to begin partitioning
    // with row in the order it was generated
    uint16_t sortedRowIndices[1024];
    for(unsigned int i = 0; i < 1024; i++)
    {
      sortedRowIndices[i] = (uint16_t)i;
    }

    // First sub-row starts at next ragged address
    uint32_t *rowAddress = raggedMatrixAddress;

    // There is no previous sub-row at this point
    uint32_t *previousSubRowDelayAddress = NULL;
    uint32_t previousSubRowStartDelay = 0;

    // Loop through possible sub-row delay ranges
    uint16_t *subRowStartIndex = &sortedRowIndices[0];
    uint16_t *subRowEndIndex = &sortedRowIndices[numIndices];
    for(int32_t startDelay = 0; subRowStartIndex != subRowEndIndex; startDelay += 7)
    {
      // Is this the first sub-row?
      const bool firstSubRow = (startDelay == 0);
      const int32_t endDelay = startDelay + 7;

      // Indirectly partition the delays to determine which are in current sub-row
      uint16_t *newSubRowStartIndex = std::partition(subRowStartIndex, subRowEndIndex,
        [delays, endDelay](uint16_t i)
        {
          return delays[i] < endDelay;
        }
      );

      // Calculate the number of synapses in this section of the sub-row
      const unsigned int numSubRowSynapses = newSubRowStartIndex - subRowStartIndex;

      // If there are any synapses in the sub-row or
      // this is the first sub-row - which is always written
      if(numSubRowSynapses != 0 || firstSubRow)
      {
        LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\t\tSub-row (%08x) with delay [%u, %u) - %u synapses",
          rowAddress, startDelay, endDelay, numSubRowSynapses);

        // If this is the first sub-row and we have exceeded
        // the maximum number of synapses per ragged-row
        if(firstSubRow && numSubRowSynapses > maxRowSynapses)
        {
          LOG_PRINT(LOG_LEVEL_ERROR, "Generated matrix with %u synapses in first sub-row when maximum is %u",
                    numSubRowSynapses, maxRowSynapses);
          return false;
        }

        // If this row is going to go past end of memory allocated for matrix
        if(rowAddress > endAddress)
        {
          LOG_PRINT(LOG_LEVEL_ERROR, "Matrix overflowed memory allocated for it");
          return false;
        }

        // If this isn't the first sub-row
        if(!firstSubRow)
        {
          // Build a row offset-length object based on this row's number of
          // synapses and its offset from the start of the matrix
          RowOffsetLength rowOffsetLength(numSubRowSynapses,
                                          rowAddress - synapticMatrixBaseAddress);

          // Write row's delay offset and the word representation of it's
          // offset and length to the correct part of the previous sub-row
          previousSubRowDelayAddress[0] = startDelay - previousSubRowStartDelay;
          previousSubRowDelayAddress[1] = rowOffsetLength.GetWord();
        }

        // Write number of indices in sub-row to correct address
        *rowAddress++ = numSubRowSynapses;

        // The next sub-row will want to write its delay details
        // here so cache its pointer and uint32_t *synapticMatrixBaseAddress, its starting delay
        previousSubRowDelayAddress = rowAddress;
        previousSubRowStartDelay = startDelay;

        // BUT, incase they don't zero delay extension entries
        *rowAddress++ = 0;
        *rowAddress++ = 0;

        // Loop through newly-sorted sub-row indices
        for(uint16_t *j = subRowStartIndex; j != newSubRowStartIndex; j++)
        {
          // Extract index pointed to by sorted index
          const uint32_t postIndex = indices[*j];

          // Clamp delays and weights pointed to be sorted index
          const int32_t delay = ClampDelay(delays[*j] - startDelay);
          const int32_t weight = ClampWeight(weights[*j]);

          // Build synaptic word
          const uint32_t word = (postIndex & IndexMask) |
            (((uint32_t)delay & DelayMask) << IndexBits) |
            (weight << (DelayBits + IndexBits));

#if LOG_LEVEL <= LOG_LEVEL_TRACE
          io_printf(IO_BUF, "%u,", word);
#endif
          // Write word to matrix
          *rowAddress++ = word;
        }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
        io_printf(IO_BUF, "\n");
#endif

        // If this is the first delay sub-row, advance the
        // ragged matrix past the padded row and update row
        // address so it writes to the start of the delay matrix
        if(firstSubRow)
        {
          raggedMatrixAddress += (3 + maxRowSynapses);
          rowAddress = delayMatrixAddress;
        }
        // Otherwise, advance the delay matrix address past
        // the sub-row and update row-address so it writes here
        else
        {
          delayMatrixAddress += (3 + numSubRowSynapses);
          rowAddress = delayMatrixAddress;
        }
      }

      // Advance to next sub-row
      subRowStartIndex = newSubRowStartIndex;
    }
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tGenerated %u synapses", numSynapses);
  return true;
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator::Plastic
//-----------------------------------------------------------------------------
ConnectionBuilder::MatrixGenerator::Plastic::Plastic(uint32_t *&region) : Base(region)
{
  // Read number of presynaptic state words from region
  const uint32_t preStateBytes = *region++;
  m_SynapseTraceBytes = *region++;

  // Round up to words
  m_PreStateWords = (preStateBytes / 4)
      + (((preStateBytes & 3) != 0) ? 1 : 0);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tPlastic synaptic matrix: %u signed weights, %u bytes presynaptic state (%u words), %u bytes synapse trace",
            IsSignedWeight(), preStateBytes, m_PreStateWords, m_SynapseTraceBytes);
}
//-----------------------------------------------------------------------------
bool ConnectionBuilder::MatrixGenerator::Plastic::Generate(
  uint32_t *synapticMatrixBaseAddress, uint32_t *matrixAddress,
  unsigned int maxRowSynapses, unsigned int weightFixedPoint,
  unsigned int numPostNeurons, unsigned int sizeWords, unsigned int numRows,
  const ConnectorGenerator::Base *connectorGenerator,
  const ParamGenerator::Base *delayGenerator,
  const ParamGenerator::Base *weightGenerator,
  MarsKiss64 &rng) const
{
  // Calculate the number of words required to contain control array
  const unsigned int maxControlArrayWords = (maxRowSynapses / 2)
    + (((maxRowSynapses & 1) != 0) ? 1 : 0);

  // Calculate the number of words required to contain synapse array
  const unsigned int maxPlasticArrayBytes = maxRowSynapses * (2 + m_SynapseTraceBytes);
  const unsigned int maxPlasticArrayWords = (maxPlasticArrayBytes / 4)
    + (((maxPlasticArrayBytes & 3) != 0) ? 1 : 0);
  LOG_PRINT(LOG_LEVEL_INFO, "\t\tMax control array words:%u, Max synapse array words:%u",
            maxControlArrayWords, maxPlasticArrayWords);

  // Loop through rows
  unsigned int numSynapses = 0;
  for(unsigned int i = 0; i < numRows; i++)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\t\tRow %u (%08x)", i, matrixAddress);

    // Generate indices, weights and delays for row
    uint32_t indices[1024];
    int32_t delays[1024];
    int32_t weights[1024];
    const unsigned int numIndices = GenerateRow(i,
      weightFixedPoint, numPostNeurons, connectorGenerator, delayGenerator,
      weightGenerator, indices, delays, weights, rng);

    // Update total number of synapses
    numSynapses += numIndices;

    // Write row length
    *matrixAddress++ = numIndices;

    // **TODO** support delay extension
    *matrixAddress++ = 0;
    *matrixAddress++ = 0;

    // Zero presynaptic state words
    for(unsigned int w = 0; w < m_PreStateWords; w++)
    {
      *matrixAddress++ = 0;
    }

    // Calculate the size of each array (fixed and plastic) in words
    const unsigned int numSynapseArrayBytes = numIndices * (2 + m_SynapseTraceBytes);
    const unsigned int numPlasticArrayWords = (numSynapseArrayBytes / 4)
      + (((numSynapseArrayBytes & 3) != 0) ? 1 : 0);

    // From this get 8-bit pointer to synapses and 16-bit pointer to control half words
    uint8_t *synapseAddress = reinterpret_cast<uint8_t*>(matrixAddress);
    uint16_t *controlAddress = reinterpret_cast<uint16_t*>(matrixAddress + numPlasticArrayWords);

    // Loop through synapses
    for(unsigned int j = 0; j < numIndices; j++)
    {
      // Clamp delays and weights
      delays[j] = ClampDelay(delays[j]);
      weights[j] = ClampWeight(weights[j]);

      // Write weight to first two synapse bytes
      uint16_t *weightAddress = reinterpret_cast<uint16_t*>(synapseAddress);
      *weightAddress = (uint16_t)weights[j];

      // Go onto next synapse
      synapseAddress += 2;

      // Write synapse trace bytes
      for(unsigned int s = 0; s < m_SynapseTraceBytes; s++)
      {
        *synapseAddress++ = 0;
      }

      // Build control word
      const uint16_t controlWord = (uint16_t)(indices[j] & IndexMask) |
        (((uint32_t)delays[j] & DelayMask) << IndexBits);

#if LOG_LEVEL <= LOG_LEVEL_TRACE
      io_printf(IO_BUF, "%u/%u,", weights[j], controlWord);
#endif
      // Write control word
      *controlAddress++ = controlWord;
    }

#if LOG_LEVEL <= LOG_LEVEL_TRACE
    io_printf(IO_BUF, "\n");
#endif

    // Advance over synapse and control half words; and padding to next word
    matrixAddress += (maxControlArrayWords + maxPlasticArrayWords);
  }

  LOG_PRINT(LOG_LEVEL_INFO, "\t\tGenerated %u synapses", numSynapses);
  return true;
}
