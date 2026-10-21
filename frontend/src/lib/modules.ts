import type { IconName } from './ui/icons';

export type Accent = 'lavender' | 'mint' | 'peach' | 'butter' | 'sky' | 'rose' | 'paper';

export type AppModule = {
	label: string;
	href: string;
	icon: IconName;
	accent: Accent;
	/** Shown in the phone dock (settings lives in the top bar there). */
	inDock: boolean;
};

// Each module keeps one pastel everywhere: title bars, calendar chips, charts.
export const modules: AppModule[] = [
	{ label: 'Home', href: '/', icon: 'home', accent: 'lavender', inDock: true },
	{ label: 'Calendar', href: '/calendar', icon: 'calendar', accent: 'lavender', inDock: true },
	{ label: 'To-dos', href: '/todos', icon: 'todo', accent: 'butter', inDock: true },
	{ label: 'Workouts', href: '/workouts', icon: 'workout', accent: 'mint', inDock: true },
	{ label: 'Expenses', href: '/expenses', icon: 'expense', accent: 'peach', inDock: true },
	{ label: 'Ideas', href: '/ideas', icon: 'idea', accent: 'sky', inDock: true },
	{ label: 'Settings', href: '/settings', icon: 'settings', accent: 'paper', inDock: false }
];

export function isActive(module: AppModule, pathname: string): boolean {
	return module.href === '/' ? pathname === '/' : pathname.startsWith(module.href);
}

export function currentModule(pathname: string): AppModule | undefined {
	return modules.find((m) => isActive(m, pathname));
}

export function accentVar(accent: Accent): string {
	return accent === 'paper' ? 'var(--color-surface)' : `var(--color-${accent})`;
}
