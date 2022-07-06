'use strict';
(async () => {
	async function fetchTalents() {
		const res = await fetch('/data/talents');
		return await res.json();
	}
	const talents = await fetchTalents();
	const selectedTalents = {};

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

	const tree = document.querySelector('main div.tree');
	const info = document.querySelector('main div.info');
	function showTree(index) {
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

			tree.appendChild(talentDiv);
		}
	}

	tree.addEventListener('click', (event) => {
		const key = treeClickTalentKey(event.target);
		if (key)
			handleTalentClick(key, true);
	});
	tree.addEventListener('contextmenu', (event) => {
		const key = treeClickTalentKey(event.target);
		if (key) {
			event.preventDefault();
			handleTalentClick(key, false);
		}
	});

	function treeClickTalentKey(target) {
		if (event.target.tagName == 'IMG')
			target = target.parentElement;
		return target.dataset.key;
	}

	function handleTalentClick(key, incr) {
		const talent = talents['talents'][key];
		showTalentInfo(talent);

		// type/class: 3 bits
		// tier: 4 bits
		// position: 3 bits
		// total of 10 bits
		const urlKey = (talent['Type'] << 7) | (talent['tier'] << 3) | (talent['Position']);

		if (incr) {
			if (selectedTalents[urlKey] === undefined)
				selectedTalents[urlKey] = 1;
			else if (selectedTalents[urlKey] < talent['maxLevel'])
				selectedTalents[urlKey]++;
		} else {
			if (selectedTalents[urlKey] > 1)
				selectedTalents[urlKey]--;
			else
				delete selectedTalents[urlKey];
		}

		history.replaceState({}, '', '/build/?s=' + JsonURL.stringify({'talents': selectedTalents},  {AQF: true}));
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

	showTree(0);
})();
