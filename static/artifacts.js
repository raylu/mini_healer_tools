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
			const keys = JSON.parse(dataset.keys);
			resultsCB(keys, dataset.name);
		});

		searchInput.addEventListener('blur', (event) => {
			if (this.searchTimeout !== null)
				clearTimeout(this.searchTimeout);
			// wait long enough to allow clicks on results
			setTimeout(() => results.classList.remove('visible'), 100);
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
				result.dataset.keys = JSON.stringify(keys);
				results.appendChild(result);
			}
		}
		results.classList.add('visible');
	}

	async load(key, anomaly, section) {
		let url = '/data/artifact/' + key;
		if (anomaly > 0)
			url += '?anomaly=' + anomaly;
		const res = await fetch(url);
		const artifact = await res.json();

		const rarity = this.rarities[artifact['Rarity']];

		const icon = document.createElement('div');
		icon.classList.add('icon');
		if (artifact['isRuneword'])
			icon.style.backgroundImage = 'url(/static/runes.png)';
		else {
			let iconFilename = artifact['Key'];
			if (anomaly) iconFilename += '_ANOMALY' + anomaly;
			icon.style.backgroundImage = `url(/static/artifacts/${iconFilename}.png)`;
		}
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
		const types = [];
		if (artifact['isRuneword'])
			types.push('Runic');
		else {
			types.push(this.types[artifact['Type']]);
			if (artifact['Rarity']) types.push(rarity);
		}
		if (artifact['isUltraRare']) types.push('Ultra Rare');
		if (artifact['isChaotic']) types.push('Chaotic');
		type.innerHTML = types.join(', ');
		type.classList.add('type');
		section.appendChild(type);

		const desc = document.createElement('div');
		desc.classList.add('desc');
		const replace = (needle) => {
			const textVar = needle.substr(1, needle.length - 2);
			const replacement = artifact['strings'][textVar];
			if (!replacement)
				return needle;
			else if (textVar.substring(0, 5) === 'LINK_')
				return `<span class="link">${replacement}</span>`;
			else
				return replacement;
		};
		for (const attr of artifact['attributes']) {
			const sign = attr['is_negative'] ? '' : '+';
			let number = attr['t1_min'].toString();
			if (attr['t1_min'] !== attr['t1_max'])
				number = `${attr['t1_min']} to ${attr['t1_max']}`;
			const attribute = attr['text'].replaceAll(/\[\S+\]/g, replace);
			let line = `${sign}${number}`;
			if (attribute[0] !== '%')
				line += ' ';
			if (attr['ref_id'])
				line += `<span class="link">${attribute}</span>`;
			else
				line += attribute;
			if (attr['postText'])
				line += ' ' + attr['postText'];
			if (attr['element'] !== null)
				line = `<span class="${attr['element']}">${line}</span>`;
			desc.innerHTML += line + '<br>';
		}
		if (artifact['description'])
			desc.innerHTML += '<br>' + artifact['description'].replaceAll(/\[\S+\]/g, replace);
		section.appendChild(desc);

		const propHTML = [];
		if (artifact['HiddenItemLevel'])
			propHTML.push('item level: ' + artifact['HiddenItemLevel']);
		if (artifact['droppedBossName']) {
			propHTML.push('dropped by: ' + artifact['droppedBossName']);
			propHTML.push('difficulty: ' + artifact['droppedBossDifficulty']);
		}
		if (artifact['DropRate']) {
			const dropRate = artifact['DropRate'].toLocaleString(undefined,
				{'minimumFractionDigits': 1, 'style': 'percent'});
			propHTML.push('drop rate: ' + dropRate);
		}
		if (artifact['isRuneword'])
			propHTML.push('runes: ' + artifact['runes'].join(', '));
		const props = document.createElement('div');
		props.classList.add('props');
		props.innerHTML = propHTML.join('<br>');
		section.appendChild(props);

		const icons = document.createElement('div');
		icons.classList.add('icons');
		if (artifact['isChaotic'])
			this.#addIcon(icons, 'chaotic');
		if (artifact['isDivine'])
			this.#addIcon(icons, 'divine');
		else if (artifact['isDivinable'])
			this.#addIcon(icons, 'divinable');
		if (anomaly)
			this.#addIcon(icons, 'anomalous');
		section.appendChild(icons);
	}

	#addIcon(container, name) {
		const icon = document.createElement('img');
		icon.src = `/static/artifact_${name}.png`;
		container.appendChild(icon);
	}
}

(async () => {
	if (window.location.pathname.substring(0, 10) !== '/artifacts')
		return;

	const artifacts = new Artifacts();
	await artifacts.fetchArtifactNames();
	artifacts.setupSearch(resultsCB);

	function handlePopState() {
		const name = decodeURIComponent(window.location.pathname.substring(11));
		loadKeys(artifacts.artifactNames[name]['keys']);
		const searchInput = document.querySelector('form#search input[name=q]');
		searchInput.value = name;
	}
	if (window.location.pathname.substring(0, 11) === '/artifacts/') {
		handlePopState();
		addEventListener('popstate', handlePopState);
	}

	function resultsCB(keys, name) {
		history.pushState({}, '', '/artifacts/' + name);
		loadKeys(keys);
	}

	function loadKeys(keys) {
		const main = document.querySelector('main');
		main.innerHTML = '';
		for (const key of keys) {
			for (let anomaly = 0; anomaly <= (key['maxAnomaly'] || 0); anomaly++) {
				const section = document.createElement('section');
				section.classList.add('artifact');
				artifacts.load(key['key'], anomaly, section);
				main.appendChild(section);
			}
		}
	}
})();
