function sendData() {
    const task = document.getElementById("task").value;

    fetch('/add_entry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task: task })
    })
    .then(response => response.json())
    .then(data => {
        const responseDiv = document.getElementById('response');

        // Convert list of dicts into a string
        const output = data.map(item => item.date).join(', ');

        responseDiv.innerText = output;
    })
    .catch(error => {
        console.error('Error', error);
    });
}
