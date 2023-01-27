<script>
	import { onMount } from 'svelte';
	import { json } from 'd3';
	let features = {};
	onMount(async () => {
		let res = json(data.json);
		let newFeatures = {};
		for (let key in raw.objects) {
			newFeatures[key] = topojson.feature(raw, raw.objects[key]);
		}

		features = newFeatures;
	});
</script>

{console.log(features)}
