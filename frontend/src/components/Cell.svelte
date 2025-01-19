<script>
  import { createEventDispatcher } from 'svelte';
  export let row;
  export let col;
  export let value = '';
  const dispatch = createEventDispatcher();
  let editing = false;
  let inputValue;

  // Synchronize inputValue with value when not editing
  $: if (!editing) {
    inputValue = value;
  }

  function handleDoubleClick() {
    editing = true;
    // Ensure inputValue is synced with value when editing starts
    inputValue = value;
  }

  function handleBlur() {
    editing = false;
    if (inputValue !== value) {
      dispatch('update', inputValue);
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter') {
      editing = false;
      if (inputValue !== value) {
        dispatch('update', inputValue);
      }
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
