#pragma once

// Standard includes
#include <new>

// Macros
#define ADD_FACTORY_CREATOR(T)                         \
  static Base *Create(uint32_t *&region, void *memory) \
  {                                                    \
    return new(memory) T(region);                      \
  }

#define REGISTER_FACTORY_CLASS(G, T) \
  g_##G##Factory.Register(G##Type##T, G::T::Create, sizeof(G::T))

//-----------------------------------------------------------------------------
// ConnectionBuilder
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
//-----------------------------------------------------------------------------
// GeneratorFactory
//-----------------------------------------------------------------------------
template<typename B, unsigned int N>
class GeneratorFactory
{
public:
  //-----------------------------------------------------------------------------
  // Typedefines
  //----------------------------------------------------------------------------
  typedef B* (*CreateGeneratorFunction)(uint32_t *&, void*);

  //----------------------------------------------------------------------------
  // Static methods
  //----------------------------------------------------------------------------
  B* Create(unsigned int i, uint32_t *&region, void *memory)
  {
    // If i is approximately valid
    if(i < N)
    {
      // Get function from table
      auto createGeneratorFunction = m_CreateGeneratorFunctions[i];

      // If function is found
      if(createGeneratorFunction != NULL)
      {
        return createGeneratorFunction(region, memory);
      }
      else
      {
        LOG_PRINT(LOG_LEVEL_ERROR, "Cannot create generator with ID:%u in factory - Not registered",
                i);
      }
    }
    else
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Cannot create generator with ID:%u in factory supporting:%u",
                i, N);
    }

    return NULL;
  }

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

  bool Register(unsigned int i, CreateGeneratorFunction function,
                                unsigned int classSize)
  {
    // If ID is within size of table
    if(i < N)
    {
      // If no generator function is already registered in this slot
      if(m_CreateGeneratorFunctions[i] == NULL)
      {
        // Store function in table
        m_CreateGeneratorFunctions[i] = function;

        // Update memory size
        if(classSize > m_MemorySize)
        {
          m_MemorySize = classSize;
        }

        return true;
      }
      else
      {
        LOG_PRINT(LOG_LEVEL_ERROR, "Cannot register generator with ID:%u in factory - ID already used",
                i);
      }
    }
    else
    {
      LOG_PRINT(LOG_LEVEL_ERROR, "Cannot register generator with ID:%u in factory supporting:%u",
                i, N);
    }

    return false;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  CreateGeneratorFunction m_CreateGeneratorFunctions[N];
  unsigned int m_MemorySize;
};

} // ConnectionBuilder