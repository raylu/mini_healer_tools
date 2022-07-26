'use strict';
/* global Artifacts, JsonURL, reef */
(async () => {
	async function fetchTalents() {
		const res = await fetch('/data/talents');
		return await res.json();
	}
	const talents = await fetchTalents();
	const build = reef.store(parseURL());

	const classes = {
		'Druid': 0,
		'Priest': 1,
		'Occultist': 2,
		'Paladin': 5,
	};
	function renderHeader() {
		// map class numbers to points spent in that class
		const classPoints = Object.fromEntries(Object.values(classes).map(clNum => [clNum, 0]));
		for (const [urlKey, count] of Object.entries(build['talents']))
			classPoints[urlKey >> 7] += count;

		const headers = Object.entries(classes).map(([cl, i]) => {
			const points = classPoints[i];
			if (points > 0)
				return `<h2 data-treeindex="${i}">${cl} (${points})</h2>`;
			else
				return `<h2 data-treeindex="${i}">${cl}</h2>`;
		});
		headers.push('<h2>Items</h2>');
		return headers.join('');
	}
	document.querySelector('header').addEventListener('click', (event) => {
		if (event.target.tagName != 'H2')
			return;
		const treeIndex = event.target.dataset.treeindex;
		if (treeIndex === undefined)
			showItems();
		else
			showTree(Number(treeIndex));
	});
	reef.component('header', renderHeader);

	const artifacts = new Artifacts();
	await artifacts.fetchArtifactNames();
	artifacts.setupSearch(artifactsCB);

	function parseURL() {
		let parsedBuild = {
			'talents': {},
			'items': [],
		};
		if (location.search.substr(0, 3) === '?s=') {
			parsedBuild = JsonURL.parse(location.search.substr(3), {AQF: true, noEmptyComposite: true});
		}
		return parsedBuild;
	}
	function updateURL(buildData) {
		history.replaceState({}, '', '/build/?s=' + JsonURL.stringify(buildData, {AQF: true, noEmptyComposite: true}));
	}

	const main = document.querySelector('main');
	const tree = document.querySelector('main div.tree');
	const info = document.querySelector('main div.info');
	const items = document.querySelector('main div.items');
	let currentTree = null;
	function showTree(index) {
		main.innerHTML = '';
		tree.innerHTML = '';
		info.innerHTML = '';
		main.appendChild(tree);
		main.appendChild(info);

		if (currentTree !== null)
			currentTree['component'].stop();
		currentTree = {'index': index};
		currentTree['component'] = reef.component('main div.tree', renderTree);
	}
	function renderTree() {
		const {index} = currentTree;
		const divs = [];
		for (const talent of Object.values(talents['talents'])) {
			if (talent['Type'] !== index)
				continue;

			const points = build['talents'][talentUrlKey(talent)] || 0;
			const classes = ['talent'];
			if (points > 0) {
				classes.push('allocated');
				if (points === talent['maxLevel'])
					classes.push('maxed');
			}
			divs.push(`<div class="${classes.join(' ')}" data-key="${talent['Key']}"
					style="grid-row: ${talent['tier']}; grid-column: ${talent['Position'] + 1}">
				<img src="/static/talents/${talent['Key']}.png">
				${points}
			</div>`);
		}
		return divs.join('');
	}

	tree.addEventListener('click', (event) => handleTalentClick(event, true));
	tree.addEventListener('contextmenu', (event) => handleTalentClick(event, false));

	function handleTalentClick(event, incr) {
		let target = event.target;
		if (event.target.tagName == 'IMG')
			target = target.parentElement;
		const key = target.dataset.key;
		if (!key)
			return;
		if (!incr)
			event.preventDefault();

		const talent = talents['talents'][key];
		showTalentInfo(talent);

		const urlKey = talentUrlKey(talent);
		const selectedTalents = build['talents'];
		let points = selectedTalents[urlKey] || 0;
		if (incr) {
			if (points < talent['maxLevel'])
				points++;
		} else {
			if (points > 0)
				points--;
		}
		if (points > 0)
			selectedTalents[urlKey] = points;
		else
			delete selectedTalents[urlKey];

		updateURL(build);
	}

	function talentUrlKey(talent) {
		// type/class: 3 bits
		// tier: 4 bits
		// position: 3 bits
		// total of 10 bits
		return (talent['Type'] << 7) | (talent['tier'] << 3) | (talent['Position']);
	}

	function showTalentInfo(talent) {
		info.innerHTML = '';

		const name = document.createElement('h2');
		name.innerText = talent['TalentName'];
		info.appendChild(name);

		if (talent['desc']) {
			const desc = document.createElement('div');
			desc.classList.add('desc');
			const replace = (needle) => {
				const textVar = needle.substr(1, needle.length - 2);
				const replacement = talents['strings'][textVar];
				return replacement ? replacement : needle;
			};
			desc.innerHTML = talent['desc'].replaceAll(/\[\S+\]/g, replace);
			info.appendChild(desc);
		}

		const extra = document.createElement('div');
		extra.classList.add('extra');
		extra.innerText = `Maximum of ${talent['maxLevel']} levels`;
		info.appendChild(extra);
	}

	const pendingItem = document.querySelector('main .items #pending_item');
	const selectedItems = document.querySelector('main .items #selected_items');
	function showItems() {
		if (currentTree !== null)
			currentTree['component'].stop();

		if (selectedItems.childElementCount === 0) {
			// this may be the first time we're showing items
			for (const [key, anomaly] of build['items']) {
				const section = document.createElement('section');
				section.classList.add('artifact');
				section.dataset['key'] = key;
				section.dataset['anomaly'] = anomaly;
				artifacts.load(key, anomaly, section);
				renderSelectedItem(section);
			}
		}

		main.innerHTML = '';
		main.appendChild(items);
	}

	function artifactsCB(keys, name) {
		pendingItem.innerHTML = '';
		for (const key of keys) {
			for (let anomaly = 0; anomaly <= (key['maxAnomaly'] || 0); anomaly++) {
				const section = document.createElement('section');
				section.classList.add('artifact');
				section.dataset['key'] = key['key'];
				section.dataset['anomaly'] = anomaly;
				artifacts.load(key['key'], anomaly, section);
				pendingItem.appendChild(section);
			}
		}
	}

	pendingItem.addEventListener('click', (event) => {
		let target = event.target;
		let found = false;
		while (target.id !== 'pending_item') {
			if (target.tagName === 'SECTION' && target.classList.contains('artifact')) {
				found = true;
				break;
			}
			target = target.parentElement;
		}
		if (!found) return;

		pendingItem.innerHTML = '';
		renderSelectedItem(target);

		const key = target.dataset['key'];
		const anomaly = Number(target.dataset['anomaly']);
		build['items'].push([key, anomaly]);
		updateURL(build);
	});

	function renderSelectedItem(element) {
		const deleteDiv = document.createElement('div');
		deleteDiv.classList.add('delete');
		deleteDiv.innerHTML = '✖';
		element.appendChild(deleteDiv);
		selectedItems.appendChild(element);
	}

	selectedItems.addEventListener('click', (event) => {
		if (event.target.tagName !== 'DIV' || !event.target.classList.contains('delete'))
			return;

		const section = event.target.parentElement;
		section.remove();

		build['items'] = build['items'].filter(([key, anomaly]) =>
			key !== section.dataset['key'] || anomaly !== section.dataset['anomaly']);
		updateURL(build);
	});

	document.querySelector('form#build').addEventListener('formdata', (event) => {
		event.formData.set('build', JSON.stringify(build));
	});

	document.querySelector('form#build input#reset').addEventListener('click', (event) => {
		Object.assign(build, {
			'talents': {},
			'items': [],
		});
		updateURL(build);
		showTree(0);
	});

	showTree(0);
})();
