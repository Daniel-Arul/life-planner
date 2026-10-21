/**
 * Whether the planner on the Pi answered the last request. It goes false when
 * the network fails (Tailscale off, no signal) or the proxy says the app is down.
 */
class Connection {
	reachable = $state(true);
}

export const connection = new Connection();
