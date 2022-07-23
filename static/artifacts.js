'use strict';

class Artifacts {
	constructor() {
		this.artifactNames = null;
		this.searchTimeout = null;

		this.types = {
			// slot 0
			0: 'Axe',
			1: 'Sword',
			2: 'Wand',
			3: 'Bow',
			9: 'Dagger',
			10: 'Claw',
			14: 'Staff',
			15: 'Hammer',
			// slot 1
			4: 'Shield',
			5: 'Body Armor',
			6: 'Helm',
			7: 'Glove',
			17: 'Boot',
			19: 'Pants',
			// slot 2
			8: 'Relic',
			11: 'Arrow',
			12: 'Ring',
			13: 'Amulet',
			// special
			16: 'Belt',
			20: 'Map',
		};
		this.rarities = {
			0: 'Uncommon',
			1: 'Rare',
			2: 'Epic',
			3: 'Unique',
		};
	}

	async fetchArtifactNames() {
		const res = await fetch('/data/artifact_names');
		this.artifactNames = await res.json();
	}

	setupSearch(resultsCB) {
		const searchInput = document.querySelector('form#search input[name=q]');
		searchInput.addEventListener('input', (event) => {
			const q = event.target.value;
			if (this.searchTimeout !== null)
				clearTimeout(this.searchTimeout);
			this.searchTimeout = setTimeout(() => this.search(q), 200);
		});

		const results = document.querySelector('div#results');
		results.addEventListener('click', (event) => {
			results.classList.remove('visible');
			results.innerHTML = '';
			const dataset = event.target.dataset;
			const keys = dataset.keys.split(',');
			resultsCB(keys, dataset.name);
		});

		document.querySelector('form#search').addEventListener('blur', (event) => {
			if (this.searchTimeout !== null)
				clearTimeout(this.searchTimeout);
			results.classList.remove('visible');
		});
	}

	search(q) {
		const results = document.querySelector('div#results');
		results.innerHTML = '';
		q = q.toLowerCase();
		for (const [name, {keys, rarity}] of Object.entries(this.artifactNames)) {
			if (name.toLowerCase().indexOf(q) !== -1) {
				const result = document.createElement('div');
				result.classList.add('result');
				if (this.rarities[rarity])
					result.classList.add(this.rarities[rarity].toLowerCase());
				result.innerText = name;
				result.dataset.name = name;
				result.dataset.keys = keys;
				results.appendChild(result);
			}
		}
		results.classList.add('visible');
	}

	async load(key, section) {
		const res = await fetch('/data/artifact/' + key);
		const artifact = await res.json();

		const rarity = this.rarities[artifact['Rarity']];

		const icon = document.createElement('div');
		icon.classList.add('icon');
		icon.style.backgroundImage = `url(/static/artifacts/${artifact['Key']}.png)`;
		const img = document.createElement('img');
		img.src = '/static/artifact_frame.png';
		img.classList.add(rarity.toLowerCase());
		icon.appendChild(img);
		section.appendChild(icon);

		const name = document.createElement('h2');
		name.innerText = artifact['ArtifactName'];
		name.classList.add(rarity.toLowerCase());
		section.appendChild(name);

		const type = document.createElement('div');
		const types = [
			this.types[artifact['Type']],
		];
		if (artifact['Rarity']) types.push(rarity);
		if (artifact['isUltraRare']) types.push('Ultra Rare');
		if (artifact['isChaotic']) types.push('Chaotic');
		type.innerHTML = types.join(', ');
		type.classList.add('type');
		section.appendChild(type);

		if (artifact['specialDesc']) {
			const desc = document.createElement('div');
			const replace = (needle) => {
				const textVar = needle.substr(1, needle.length - 2);
				const replacement = artifact['strings'][textVar];
				return replacement ? replacement : needle;
			};
			desc.innerHTML = artifact['specialDesc'].replaceAll(/\[\S+\]/g, replace);
			desc.classList.add('desc');
			section.appendChild(desc);
		}

		const props = document.createElement('div');
		if (artifact['HiddenItemLevel'])
			props.innerHTML += 'item level: ' + artifact['HiddenItemLevel'];
		if (artifact['DropRate'])
			props.innerHTML += '<br>drop rate: ' + artifact['DropRate'] * 100 + '%';
		props.classList.add('props');
		section.appendChild(props);
	}
}

(async () => {
	if (window.location.pathname.substr(0, 10) !== '/artifacts')
		return;

	const artifacts = new Artifacts();
	await artifacts.fetchArtifactNames();
	artifacts.setupSearch(resultsCB);

	if (window.location.pathname.substr(0, 11) === '/artifacts/') {
		const name = decodeURIComponent(window.location.pathname.substr(11));
		loadKeys(artifacts.artifactNames[name]['keys']);
		const searchInput = document.querySelector('form#search input[name=q]');
		searchInput.value = name;
	}

	function resultsCB(keys, name) {
		history.pushState({}, '', '/artifacts/' + name);
		loadKeys(keys);
	}

	function loadKeys(keys) {
		const main = document.querySelector('main');
		main.innerHTML = '';
		for (const key of keys) {
			const section = document.createElement('section');
			section.classList.add('artifact');
			artifacts.load(key, section);
			main.appendChild(section);
		}
	}
})();
