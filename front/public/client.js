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
        console.log(json);

        // pillamos las posiciones del mapa
        var pos = document.getElementsByClassName('mapa');
        console.log(pos);
      } else {
        console.error('Error en la solicitud:', response.statusText);
      }

      const urlDrones = 'https://192.168.1.211:23456/dron';
      var numDrones = 

      const response = await fetch(urlDrones);

      if (response.ok) {
        const json = await response.json();
        console.log(json);

        // pillamos las posiciones del mapa
        var pos = document.getElementsByClassName('mapa');
        console.log(pos);
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
