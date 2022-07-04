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
			main.appendChild(section);
			load(key, section);
		}
	}

	const slots = {
		0: {
			0: 'Axe',
			1: 'Sword',
			2: 'Wand',
			3: 'Bow',
			9: 'Dagger',
			14: 'Staff',
			15: 'Hammer',
		},
		1: {
			4: 'Shield',
			5: 'Body Armor',
			6: 'Helm',
			7: 'Glove',
			17: 'Boot',
			19: 'Pants',
		},
		2: {
			8: 'Relic',
			11: 'Arrow',
			12: 'Ring',
			13: 'Amulet',
		},
	}
	const rarities = {
		3: 'Unique',
	}

	async function load(key, section) {
		const res = await fetch('/data/artifact/' + key);
		const artifact = await res.json();

		const name = document.createElement('h2');
		name.innerText = artifact['ArtifactName'];
		section.appendChild(name);

		const type = document.createElement('div');
		const types = [
			slots[artifact['SlotType']][artifact['Type']],
		];
		if (artifact['Rarity']) types.push(rarities[artifact['Rarity']]);
		if (artifact['isUltraRare']) types.push('Ultra Rare');
		if (artifact['isChaotic']) types.push('Chaotic');
		type.innerHTML = types.join(', ');
		type.classList.add('type')
		section.appendChild(type);

		if (artifact['specialDesc']) {
			const desc = document.createElement('div');
			const replace = (needle) => {
				const textVar = needle.substr(1, needle.length - 2);
				const replacement = artifact['strings'][textVar];
				return replacement ? replacement : needle;
			};
			desc.innerHTML = artifact['specialDesc'].replaceAll(/\[\S+\]/g, replace);
			desc.classList.add('desc')
			section.appendChild(desc);
		}

		const props = document.createElement('div');
		if (artifact['HiddenItemLevel'])
			props.innerHTML += 'item level: ' + artifact['HiddenItemLevel'];
		if (artifact['DropRate'])
			props.innerHTML += '<br>drop rate: ' + artifact['DropRate'] * 100 + '%';
		props.classList.add('props')
		section.appendChild(props);
	}
})();
