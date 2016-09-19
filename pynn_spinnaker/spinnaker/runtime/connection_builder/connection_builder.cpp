#include "connection_builder.h"

// Common includes
#include "../common/config.h"
#include "../common/log.h"
#include "../common/key_lookup_binary_search.h"
#include "../common/spinnaker.h"

// Connection builder includes
#include "generator_factory.h"
#include "matrix_generator.h"

// Namespaces
using namespace Common;
using namespace ConnectionBuilder;

//-----------------------------------------------------------------------------
// Anonymous namespace
//-----------------------------------------------------------------------------
namespace
{
//----------------------------------------------------------------------------
// Module level variables
//----------------------------------------------------------------------------
Config g_Config;
KeyLookupBinarySearch<10> g_KeyLookup;

uint32_t g_AppWords[AppWordMax];

uint32_t *g_SynapticMatrixBaseAddress = NULL;

GeneratorFactory<MatrixGenerator::Base, MatrixGeneratorTypeMax> g_MatrixGeneratorFactory;

//-----------------------------------------------------------------------------
// Module functions
//-----------------------------------------------------------------------------
bool ReadSynapticMatrixRegion(uint32_t *region, uint32_t)
{
  LOG_PRINT(LOG_LEVEL_INFO, "ReadSynapticMatrixRegion");

  // Cache pointer to region as base address for synaptic matrices
  g_SynapticMatrixBaseAddress = region;

  LOG_PRINT(LOG_LEVEL_INFO, "\tSynaptic matrix base address:%08x",
            g_SynapticMatrixBaseAddress);

  return true;
}
//-----------------------------------------------------------------------------
bool ReadMatrixGenerationRegion(uint32_t *region, uint32_t)
{
  LOG_PRINT(LOG_LEVEL_INFO, "ReadMatrixGenerationRegion");

  // Loop through matrices to generate
  const uint32_t numMatricesToGenerate = *region++;
  for(unsigned int i = 0; i < numMatricesToGenerate; i++)
  {
    // Read basic matrix properties
    const uint32_t key = *region++;
    const auto matrixGenerator = g_MatrixGeneratorFactory.Create(*region++, region);
    //const uint32_t connectorType = *region++;
    //const uint32_t delayGeneratorType = *region++;
    //const uint32_t weightGeneratorType = *region++;
    //LOG_PRINT(LOG_LEVEL_INFO, "\tMatrix %u: key %08x, matrix type:%u, connector type:%u, delay generator type:%u, weight generator type:%u",
    //          key, matrixType, connectorType, delayGeneratorType, weightGeneratorType);

    // Find matrix in key lookup
    unsigned int matrixRowSynapses;
    unsigned int matrixWordOffset;
    uint32_t matrixKeyMask;
    if(g_KeyLookup.LookupMatrix(key, matrixRowSynapses, matrixWordOffset, matrixKeyMask))
    {
      // Calculate start address of matrix
      uint32_t *matrixAddress = g_SynapticMatrixBaseAddress + matrixWordOffset;

      matrixGenerator->Generate(matrixAddress, matrixRowSynapses,
                                g_AppWords[AppWordWeightFixedPoint]);

    }
    else
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "\tMatrix not found in key lookup");
      return false;
    }
  }

  return true;
}
//-----------------------------------------------------------------------------
bool ReadSDRAMData(uint32_t *baseAddress, uint32_t flags)
{
  // Verify data header
  if(!g_Config.VerifyHeader(baseAddress, flags))
  {
    return false;
  }

  // Read system region
  if(!g_Config.ReadSystemRegion(
    Config::GetRegionStart(baseAddress, RegionSystem),
    flags, AppWordMax, g_AppWords))
  {
    return false;
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tWeight fixed point:%u, Num post-neurons:%u",
      g_AppWords[AppWordWeightFixedPoint], g_AppWords[AppWordNumPostNeurons]);
  }

  // Read key lookup region
  if(!g_KeyLookup.ReadSDRAMData(
    Config::GetRegionStart(baseAddress, RegionKeyLookup),
    flags))
  {
    return false;
  }

  // Read synaptic matrix region
  if(!ReadSynapticMatrixRegion(
    Config::GetRegionStart(baseAddress, RegionSynapticMatrix),
    flags))
  {
    return false;
  }


  return true;
}
} // anonymous namespace

//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
extern "C" void c_main()
{
  // Register matrix generators with factories
  REGISTER_FACTORY_CLASS(MatrixGenerator, Static);

  // Allocate memory for factories
  g_MatrixGeneratorFactory.Allocate();

  // Get this core's base address using alloc tag
  uint32_t *baseAddress = Config::GetBaseAddressAllocTag();

  // If reading SDRAM data fails
  if(!ReadSDRAMData(baseAddress, 0))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data");
    return;
  }

  // Start simulation
  spin1_start(SYNC_WAIT);
}