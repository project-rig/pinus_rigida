#pragma once

// Common includes
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Common::DisableIRQ
//-----------------------------------------------------------------------------
namespace Common
{
class DisableIRQ
{
public:
  DisableIRQ()
  {
    m_StatusRegister = spin1_irq_disable();
  }

  ~DisableIRQ()
  {
    spin1_mode_restore(m_StatusRegister);
  }

  DisableIRQ(DisableIRQ const &) = delete;

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint m_StatusRegister;
};

//-----------------------------------------------------------------------------
// Common::DisableIRQFIQ
//-----------------------------------------------------------------------------
class DisableIRQFIQ
{
public:
  DisableIRQFIQ()
  {
    m_StatusRegister = spin1_irq_disable();
    spin1_fiq_disable();
  }

  ~DisableIRQFIQ()
  {
    spin1_mode_restore(m_StatusRegister);
  }

  DisableIRQFIQ(DisableIRQFIQ const &) = delete;

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint m_StatusRegister;
};

//-----------------------------------------------------------------------------
// Common::DisableFIQ
//-----------------------------------------------------------------------------
class DisableFIQ
{
public:
  DisableFIQ()
  {
    m_StatusRegister = spin1_fiq_disable();
  }

  ~DisableFIQ()
  {
    spin1_mode_restore(m_StatusRegister);
  }

  DisableFIQ(DisableFIQ const &) = delete;

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint m_StatusRegister;
};
} // namespace Common