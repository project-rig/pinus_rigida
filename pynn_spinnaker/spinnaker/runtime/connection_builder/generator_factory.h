#pragma once

// Standard includes
#include <new>

// Rig CPP common includes
#include "rig_cpp_common/compile_time_crc.h"
#include "rig_cpp_common/log.h"

// Macros
#define ADD_FACTORY_CREATOR(T)                         \
  static Base *Create(uint32_t *&region, void *memory) \
  {                                                    \
    return new(memory) T(region);                      \
  }

#define REGISTER_FACTORY_CLASS(N, G, T) \
  g_##G##Factory.Register(Common::CRC32(N), G::T::Create, sizeof(G::T))

//-----------------------------------------------------------------------------
// ConnectionBuilder
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
//-----------------------------------------------------------------------------
// GeneratorFactory
//-----------------------------------------------------------------------------
//! Implementation of the factory design pattern to create different types
//! of object (all derived off B)
//!   \tparam B   Base class of all the types this factory can create
//!   \tparam N   Maximum number of class types this factory can support
template<typename B, unsigned int N>
class GeneratorFactory
{
public:
  GeneratorFactory() : m_Count(0)
  {
  }

  //-----------------------------------------------------------------------------
  // Typedefines
  //----------------------------------------------------------------------------
  typedef B* (*CreateGeneratorFunction)(uint32_t *&, void*);

  //----------------------------------------------------------------------------
  // Static methods
  //----------------------------------------------------------------------------
  //! Create an object using the factory, initializing it using region data
  //!   \param nameHash Hash of the object type to create
  //!   \param region   Reference to pointer to data (normally located in
  //!                   SDRAM) to pass to object's constructor
  //!   \param memory   Because we want to minimize memory allocations, the
  //!                   Factory creates objects using placement new. This is
  //!                   the pointer to the area of memory (assumed to be
  //!                   allocated using Allocate and thus the right size)
  //!                   to placement new objects into.
  B* Create(uint32_t nameHash, uint32_t *&region, void *memory)
  {
    // Loop through table
    for(unsigned int i = 0; i < m_Count; i++)
    {
      // If hash is correct, return newly constructed object
      if(m_NameHashes[i] == nameHash)
      {
        return m_CreateGeneratorFunctions[i](region, memory);
      }
    }

    LOG_PRINT(LOG_LEVEL_ERROR, "Cannot create find generator for hash:%u",
              nameHash);

    return NULL;
  }

  //! Allocate a block of memory, large enough for
  //! any of the objects created by this factory
  void *Allocate()
  {
    // If there is any memory to allocate do so
    if(m_MemorySize > 0)
    {
      LOG_PRINT(LOG_LEVEL_INFO, "%u bytes required for generator factory",
                m_MemorySize);
      return spin1_malloc(m_MemorySize);
    }
    else
    {
      return NULL;
    }
  }

  //! Register a new type of class with the factory (this is typically called
  //! using the REGISTER_FACTORY_CLASS macro rather than directly)
  //!   \param nameHash   Hash associated with this class
  //!   \param function   Function to call to create object of this class
  //!                     (typically a wrapper around the class's constructor
  //!                     generated using ADD_FACTORY_CREATOR)
  //!   \param classSize  How large are objects of this class in bytes
  //!                     (as reported by sizeof)
  bool Register(uint32_t nameHash, CreateGeneratorFunction function,
                unsigned int classSize)
  {
    // If there is space in generator
    if(m_Count < N)
    {
      // Store function and hash in table
      m_CreateGeneratorFunctions[m_Count] = function;ADD_FACTORY_CREATOR
      m_NameHashes[m_Count] = nameHash;
      m_Count++;

      LOG_PRINT(LOG_LEVEL_INFO, "\tRegistering class name hash %u with factory",
                nameHash);

      // Update memory size
      if(classSize > m_MemorySize)
      {
        m_MemorySize = classSize;
      }

      return true;
    }
    else
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Cannot register generator with ID:%u - Factory table full (capacity %u)",
                nameHash, N);
    }

    return false;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  // CRC-32 name hashes of classes to create
  uint32_t m_NameHashes[N];

  // Function pointers to create objects
  CreateGeneratorFunction m_CreateGeneratorFunctions[N];

  // How large is the largest class
  unsigned int m_MemorySize;

  // How many classes are currently registered
  unsigned int m_Count;
};

} // ConnectionBuilder