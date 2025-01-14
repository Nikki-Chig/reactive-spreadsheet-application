<!-- frontend/src/components/Spreadsheet.svelte -->
<script>
    import { onMount } from 'svelte';
    import Cell from './Cell.svelte';
    let rows = 10;
    let cols = 10;
    let data = {};
  
    // Initialize data
    for (let r = 1; r <= rows; r++) {
      for (let c = 1; c <= cols; c++) {
        data[`${r}-${c}`] = '';
      }
    }
  
    // WebSocket setup
    let ws;
  
    onMount(() => {
      ws = new WebSocket('ws://localhost:8888/ws');
  
      ws.onopen = () => {
        console.log('WebSocket connected');
        // Optionally, request initial data
        ws.send(JSON.stringify({ type: 'get_initial_data' }));
      };
  
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'update_cell') {
          const { row, col, value } = message.payload;
          data[`${row}-${col}`] = value;
        } else if (message.type === 'initial_data') {
          data = message.payload;
        }
      };
  
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
    });
  
    function handleCellUpdate(row, col, value) {
      data[`${row}-${col}`] = value;
      ws.send(JSON.stringify({
        type: 'update_cell',
        payload: { row, col, value },
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
  </style>
  
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
  