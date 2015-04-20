

//-----------------------------------------------------------------------------
// Event handler functions
//-----------------------------------------------------------------------------
static void dma_transfer_done(uint unused, uint tag)
{
  USE(unused);
  
  if(tag == dma_tag_input_read)
  {
    
  }
  else
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Dma transfer done with unknown tag %u\n", tag);
  }
}
//-----------------------------------------------------------------------------
void timer_tick(uint unused0, uint unused1)
{
  USE(unused0);
  USE(unused1);
  
  // Increment tick counter
  tick++;
  
}


//-----------------------------------------------------------------------------
// Entry point
//-----------------------------------------------------------------------------
void c_main()
{
  // Get this core's base address
  uint32_t *base_address = config_get_base_address();
  
  // If reading SDRAM data fails
  if(!read_sdram_data(base_address, 0))
  {
    LOG_PRINT(LOG_LEVEL_ERROR, "Error reading SDRAM data\n");
    return;
  }
  
  // Initialise 
  // **NOTE** tick is initialized to UINT32_MAX as ticks are advanced at
  // The START of each timer tick so it will be zeroed once time 'starts'
  tick = UINT32_MAX;
  
  // Initialize modules
  
  // Register callbacks
  spin1_callback_on(DMA_TRANSFER_DONE,  dma_transfer_done,  0);
  spin1_callback_on(TIMER_TICK,         timer_tick,         2);
  
  // Start simulation
  spin1_start(SYNC_WAIT);
}