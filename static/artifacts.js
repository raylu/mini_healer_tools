'use strict';
(async () => {
	async function fetchArtifactNames() {
		const res = await fetch('/data/artifact_names');
		return await res.json();
	}
	const artifactNames = await fetchArtifactNames();

	let searchTimeout = null;
	const searchInput = document.querySelector('form#search input[name=q]');
	searchInput.addEventListener('input', (event) => {
		const q = event.target.value;
		if (searchTimeout !== null)
			clearTimeout(searchTimeout);
		searchTimeout = setTimeout(search, 200, q);
	});

	if (window.location.pathname.substr(0, 11) === '/artifacts/') {
		const name = decodeURIComponent(window.location.pathname.substr(11));
		loadKeys(artifactNames[name]);
		searchInput.value = name;
	}

	const results = document.querySelector('div#results');
	function search(q) {
		results.innerHTML = '';
		q = q.toLowerCase()
		for (const [name, keys] of Object.entries(artifactNames)) {
			if (name.toLowerCase().indexOf(q) !== -1) {
				const result = document.createElement('div');
				result.classList.add('result');
				result.innerText = name;
				result.dataset.name = name;
				result.dataset.keys = keys;
				results.appendChild(result);
			}
		}
	}

	results.addEventListener('click', (event) => {
		results.innerHTML = '';
		const dataset = event.target.dataset;
		history.pushState({}, '', '/artifacts/' + dataset.name);
		const keys = dataset.keys.split(',');
		loadKeys(keys);
	});
	function loadKeys(keys) {
		const main = document.querySelector('main');
		main.innerHTML = '';
		for (const key of keys) {
			const section = document.createElement('section');
			section.innerText = key;
			main.appendChild(section);
			load(key, section);
		}
	}

	async function load(key, section) {
		const res = await fetch('/data/artifact/' + key);
		const artifact = await res.json();
	}
})();
