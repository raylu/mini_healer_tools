'use strict';
(async () => {
	async function fetchTalents() {
		const res = await fetch('/data/talents');
		return await res.json();
	}
	const talents = await fetchTalents();

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
			tree.appendChild(talentDiv);
		}
	}

	tree.addEventListener('click', (event) => {
		const key = event.target.dataset.key;
		if (key)
			showTalentInfo(key);
	});

	function showTalentInfo(key) {
		const talent = talents['talents'][key];
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
