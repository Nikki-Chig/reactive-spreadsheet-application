<!-- frontend/src/components/Cell.svelte -->
<script>
    import { createEventDispatcher } from 'svelte';
    export let row;
    export let col;
    export let value = '';
    const dispatch = createEventDispatcher();
    let editing = false;
    let inputValue = value;
  
    function handleDoubleClick() {
      editing = true;
    }
  
    function handleBlur() {
      editing = false;
      dispatch('update', inputValue);
    }
  
    function handleKeyDown(event) {
      if (event.key === 'Enter') {
        editing = false;
        dispatch('update', inputValue);
      }
    }
  </script>
  
  <div on:dblclick={handleDoubleClick}>
    {#if editing}
      <input
        bind:value={inputValue}
        on:blur={handleBlur}
        on:keydown={handleKeyDown}
        autofocus
      />
    {:else}
      {value}
    {/if}
  </div>
  
  <style>
    div {
      min-width: 100px;
      min-height: 30px;
    }
    input {
      width: 100%;
      height: 100%;
      box-sizing: border-box;
    }
  </style>
  