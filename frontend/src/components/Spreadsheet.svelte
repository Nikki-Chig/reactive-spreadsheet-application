<script>
  import { onMount } from 'svelte';
  import Cell from './Cell.svelte';
  let rows = 10;
  let cols = 10;
  let data = {};
  let connectionStatus = "Disconnected";

  // Initialize data
  for (let r = 1; r <= rows; r++) {
    for (let c = 1; c <= cols; c++) {
      data[`${r}-${c}`] = '';
    }
  }

  let ws;

  onMount(() => {
    ws = new WebSocket(import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8888/ws');

    ws.onopen = () => {
      connectionStatus = "Connected";
      console.log('WebSocket connected');
      ws.send(JSON.stringify({ type: 'get_initial_data' }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log("Received message:", message);
      if (message.type === 'update_cell') {
        const { row, col, value } = message.payload;
        data = { ...data, [`${row}-${col}`]: value };
      } else if (message.type === 'initial_data') {
        data = message.payload;
      }
    };

    ws.onerror = (error) => {
      connectionStatus = "Error";
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      connectionStatus = "Disconnected";
      console.log('WebSocket disconnected');
    };
  });

  function handleCellUpdate(row, col, value) {
    data = { ...data, [`${row}-${col}`]: value };
    ws.send(JSON.stringify({
      type: 'update_cell',
      payload: { row, col, value }
    }));
  }
</script>

<style>
  table {
    border-collapse: collapse;
    width: 100%;
  }
  th, td {
    border: 1px solid #ccc;
    padding: 8px;
    text-align: left;
  }
  th {
    background-color: #f2f2f2;
  }
  .status {
    margin-bottom: 1rem;
    font-weight: bold;
  }
</style>

<div class="status">Connection Status: {connectionStatus}</div>
<table>
  <thead>
    <tr>
      <th></th>
      {#each Array(cols).fill(null) as _, c}
        <th>{String.fromCharCode(65 + c)}</th>
      {/each}
    </tr>
  </thead>
  <tbody>
    {#each Array(rows).fill(null) as _, r}
      <tr>
        <th>{r + 1}</th>
        {#each Array(cols).fill(null) as _, c}
          <td>
            <Cell
              row={r + 1}
              col={c + 1}
              value={data[`${r + 1}-${c + 1}`]}
              on:update={(e) => handleCellUpdate(r + 1, c + 1, e.detail)}
            />
          </td>
        {/each}
      </tr>
    {/each}
  </tbody>
</table>
