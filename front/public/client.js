console.log('Client-side code running');

(function() {
  setInterval(async function() {
    try {
      const err = document.querySelector('.error');
      err.style.display = 'none';

      const url = 'https://192.168.1.211:23456/mapa';
      console.log('Sending request');
      
      const response = await fetch(url);

      if (response.ok) {
        const json = await response.json();
        n_dron = json['mapa'].length

        //MOSTRAR MAPA

      } else {
        console.error('Error en la solicitud:', response.statusText);
      }

      const urlDrones = 'https://192.168.1.211:23456/dron';
      
      var numDrones;

      const responseDron = await fetch(urlDrones);

      if (responseDron.ok) {
        const json = await responseDron.json();
        console.log(json);

        //MOSTRAR DRONES

      } else {
        console.error('Error en la solicitud:', response.statusText);
      }

      /*
      
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
