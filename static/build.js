'use strict';
(async () => {
	async function fetchTalents() {
		const res = await fetch('/data/talents');
		return await res.json();
	}
	const talents = await fetchTalents();
	const build = parseURL();

	const header = document.querySelector('header');
	const classes = {
		'Druid': 0,
		'Priest': 1,
		'Occultist': 2,
		'Paladin': 5,
	};
	for (const [cl, i] of Object.entries(classes)) {
		const h2 = document.createElement('h2');
		h2.innerText = cl;
		h2.dataset.treeIndex = i;
		header.appendChild(h2);
		h2.addEventListener('click', () => showTree(i));
	}
	header.appendChild(document.createElement('h2'));
	header.children[4].innerText = 'Items';
	header.children[4].addEventListener('click', showItems);
	const artifacts = new Artifacts();
	await artifacts.fetchArtifactNames();
	artifacts.setupSearch(artifactsCB);

	function parseURL() {
		let parsedBuild = {
			'talents': {},
			'items': [],
		};
		if (location.search.substr(0, 3) === '?s=') {
			parsedBuild = JsonURL.parse(location.search.substr(3), {AQF: true});
		}
		return parsedBuild;
	}
	function updateURL(buildData) {
		history.replaceState({}, '', '/build/?s=' + JsonURL.stringify(buildData, {AQF: true}));
	}

	const main = document.querySelector('main');
	const tree = document.querySelector('main div.tree');
	const info = document.querySelector('main div.info');
	const items = document.querySelector('main div.items');
	function showTree(index) {
		main.innerHTML = '';
		tree.innerHTML = '';
		info.innerHTML = '';
		for (const talent of Object.values(talents['talents'])) {
			if (talent['Type'] !== index)
				continue;
			const talentDiv = document.createElement('div');
			talentDiv.classList.add('talent');
			talentDiv.dataset.key = talent['Key'];
			talentDiv.style.gridRow = talent['tier'];
			talentDiv.style.gridColumn = talent['Position'] + 1;

			const img = document.createElement('img');
			img.src = `/static/talents/${talent['Key']}.png`
			talentDiv.appendChild(img);

			const points = build['talents'][talentUrlKey(talent)] || 0;
			talentDiv.append(points);

			tree.appendChild(talentDiv);
		}
		main.appendChild(tree);
		main.appendChild(info);
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

		target.childNodes[1].textContent = points;
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
		if (selectedItems.childElementCount === 0) {
			// this may be the first time we're showing items
			for (const key of build['items']) {
				const section = document.createElement('section');
				section.classList.add('artifact');
				section.dataset['key'] = key;
				artifacts.load(key, section);
				renderSelectedItem(section);
			}
		}

		main.innerHTML = '';
		main.appendChild(items);
	}

	function artifactsCB(keys, name) {
		pendingItem.innerHTML = '';
		for (const key of keys) {
			const section = document.createElement('section');
			section.classList.add('artifact');
			section.dataset['key'] = key;
			artifacts.load(key, section);
			pendingItem.appendChild(section);
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
		build['items'].push(key);
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

		build['items'] = build['items'].filter(key => key !== section.dataset['key']);
		updateURL(build);
	});

	showTree(0);
})();
