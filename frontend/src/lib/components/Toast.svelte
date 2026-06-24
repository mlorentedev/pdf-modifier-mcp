<script lang="ts">
	import { fly } from 'svelte/transition';

	let { message, type = 'info', onclose }: {
		message: string;
		type?: 'success' | 'error' | 'info';
		onclose: () => void;
	} = $props();

	const colors = {
		success: 'bg-green-600',
		error: 'bg-red-600',
		info: 'bg-blue-600'
	};

	const icons = {
		success: '✓',
		error: '✗',
		info: 'ℹ'
	};

	$effect(() => {
		const timer = setTimeout(onclose, 5000);
		return () => clearTimeout(timer);
	});
</script>

<div
	transition:fly={{ y: -20, duration: 300 }}
	class="fixed top-4 right-4 z-50 {colors[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 max-w-md"
>
	<span class="text-xl">{icons[type]}</span>
	<span class="flex-1">{message}</span>
	<button onclick={onclose} class="text-white/70 hover:text-white">×</button>
</div>
