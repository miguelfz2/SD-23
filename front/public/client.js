console.log('Client-side code running');

(function() {
  setInterval(async function() {
    try {
      const err = document.querySelector('.error');
      err.style.display = 'none';

      const url = 'https://192.168.1.211:23456/mapa';
      console.log('Sending request');
      var n_dron;
      const response = await fetch(url);
      var mapa_div = document.querySelector('.mapa');
      
      if (response.ok) {
        const json = await response.json();
        n_dron = json['mapa'].length;

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
      } else {
        console.error('Error en la solicitud:', response.statusText);
      }
      /*
      var urlDrones = 'https://192.168.1.211:23456/dron';
      const responseDron = await fetch(urlDrones);

      if (responseDron.ok) {
        const json = await responseDron.json();
        console.log(json);

        //MOSTRAR DRONES

      } else {
        console.error('Error en la solicitud:', response.statusText);
      }

      
      const urlLog = 'https://192.168.1.211:23456/logs';
      
      var numDrones;

      const responseDron = await fetch(urlDrones);

      if (responseDron.ok) {
        const json = await responseDron.json();
        console.log(json);

        //MOSTRAR DRONES

      } else {
        console.error('Error en la solicitud:', response.statusText);
      }
      */
    } catch (error) {
      const err = document.querySelector('.error');
      err.style.display = 'block';

      console.error(error);
    }
  }, 1000);
})();
