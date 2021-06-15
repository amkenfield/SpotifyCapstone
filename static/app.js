BASE_URL = "https://api.spotify.com/v1";

async function processForm(evt){
    evt.preventDefault();
    let playlistId = $('#playlist-id').val();

    const resp = await axios.get(`${BASE_URL}/${playlistId}`)
    console.log(resp);
}

$('#playlist-input').on('submit', async (event) => await processForm(event));