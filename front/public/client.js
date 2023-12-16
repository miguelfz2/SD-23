console.log('Client-side code running');

(function() {
  // Crear el contenedor de drones una vez fuera del intervalo
  const dronContainer = document.getElementById('dron-container');

  // Crear los elementos div para dron-info
  const dronInfos = [];
  for (let k = 1; k <= 4; k++) {  // Ajusta el número según tus necesidades
    const dronInfo = document.createElement('div');
    dronInfo.className = 'dron-info';
    dronContainer.appendChild(dronInfo);
    dronInfos.push(dronInfo);
  }

    const openLogsButton = document.getElementById('openLogsButton');

  // Agrega un controlador de eventos al botón
  openLogsButton.addEventListener('click', async function() {
    try {
      const urlLogs = 'https://192.168.1.211:23456/logs';
      const responseLogs = await fetch(urlLogs);

      if (responseLogs.ok) {
        const jsonLogs = await responseLogs.json();
        
        // Abrir una nueva pestaña con el contenido de jsonLogs
        const newTab = window.open('', '_blank');
        newTab.document.write('<html><head><title>Logs</title></head><body>');

        // Agregar divs con la información de jsonLogs
        jsonLogs['logs'].forEach(log => {
          newTab.document.write(`<div>${log}</div>`);
        });

        newTab.document.write('</body></html>');
        newTab.document.close();
      } else {
        console.error('Error en la solicitud:', responseLogs.statusText);
      }
    } catch (error) {
      console.error(error);
    }
  });
  setInterval(async function() {
    try {
      const err = document.querySelector('.error');
      err.style.display = 'none';

      const url = 'https://192.168.1.211:23456/mapa';
      console.log('Sending request');
      const response = await fetch(url);
      const mapa_div = document.querySelector('.mapa');
      
      if (response.ok) {
        const json = await response.json();
        const n_dron = json['mapa'].length;

        // Elimina el contenido existente del contenedor del mapa
        mapa_div.innerHTML = '';

        for (let i = 0; i < 20; i++) {
          for (let j = 0; j < 20; j++) {
            var isDronePosition = false;

            for (let k = 0; k < n_dron; k++) {
              var pos = json['mapa'][k][0];
              var spliteao = pos.split(",");
              var x = parseInt(spliteao[0].split("(")[1]);
              var y = parseInt(spliteao[1].split(")")[0]);

              if (i === x && j === y) {
                isDronePosition = true;
                break;
              }
            }

            var cell = document.createElement('div');
            cell.textContent = isDronePosition ? '🚁' : ''; // Emoji para posición de dron
            cell.className = isDronePosition ? 'drone' : '';
            mapa_div.appendChild(cell);
          }
        }

        // Actualizar solo el contenido de los elementos div en dronInfos
        for (let k = 1; k <= n_dron; k++) {
          var responseDron = await fetch(`https://192.168.1.211:23456/dron?data=${k}`);

          if (responseDron.ok) {
            var jsonDron = await responseDron.json();
            // Actualizar solo el contenido de cada dronInfo
            dronInfos[k - 1].textContent = `Dron ${k}: Alias - ${jsonDron.alias}, Posición - ${jsonDron.pos}`;
          } else {
            console.error('Error en la solicitud:', response.statusText);
          }
        }
      } else {
        console.error('Error en la solicitud:', response.statusText);
      }
    } catch (error) {
      const err = document.querySelector('.error');
      err.style.display = 'block';

      console.error(error);
    }
  }, 1000);
})();
