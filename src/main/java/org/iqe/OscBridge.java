package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.osc.LXOscEngine;
import heronarts.lx.osc.LXOscListener;
import heronarts.lx.osc.OscMessage;

import java.io.IOException;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.*;

/**
 * Still more private inheritance hoops to jump through, create chained TX/RX OSC bridge,
 * so we can receive clients and listen to and store output
 */
public class OscBridge {
    public static final String QUERY = "/lx/osc-query";
    private final LX lx;
    public final LXOscEngine.Transmitter txToClients;
    public final LXOscEngine.Receiver rxFromClients;
    public final LXOscEngine.Receiver rxFromLxLoopback;

    public final Map<String, OscMessage> state = new HashMap<>();
    public final Map<String, Set<LXOscListener>> listeners = new HashMap<>();

    private boolean listeningToEvents = true;

    public OscBridge(LX lx) {
        this.lx = lx;

        try {
            int txToCP = 3333, rxFromCP = 3232, rxFromLoopbackP = lx.engine.osc.transmitPort.getValuei();
            txToClients = lx.engine.osc.transmitter("0.0.0.0", txToCP);
            rxFromClients = lx.engine.osc.receiver(rxFromCP);
            rxFromLxLoopback = lx.engine.osc.receiver(rxFromLoopbackP);

            LOG.info("Initialized OSC ports, TX to Clients: {}, RX From Clients: {}, Internal RX Loopback {}",
                    txToCP, rxFromCP, rxFromLoopbackP);
        } catch (SocketException | UnknownHostException e) {
            throw new RuntimeException(e);
        }

        wire();
    }

    public void on(String path, LXOscListener listener) {
        listeners.putIfAbsent(path, new HashSet<>());
        listeners.get(path).add(listener);
    }

    public void onTrigger(String path, LXOscListener listener) {
        on(path, msg -> {
            if (msg.getFloat() > 0) listener.oscMessage(msg);
        });
    }

    public boolean toggle(String path) {
        double val = state.getOrDefault(path, new OscMessage().add(0.)).getFloat();
        val = val > 0 ? 0. : 1.0;
        command(path, val);
        return val > 0;
    }

    public void fire(String path) {
        if (!listeningToEvents) return;
        OscMessage lastMessage = state.get(path);
        if (lastMessage == null) {
            lastMessage = new OscMessage(path);
        }
        final OscMessage message = lastMessage;
        listeners.getOrDefault(path, Set.of()).forEach(l -> l.oscMessage(message));
    }

    public void command(String path) {
        command(path, 1.);
    }
    public void command(String path, float data) {
        command(path, (double) data);
    }
    public void command(String path, double data) {
        command(new OscMessage(path).add(data));
    }

    /** Obviously forward this on to the main LX OSC engine (via handleOscMessage method), but also
          store this last state, and fire our event listeners */
    public void command(OscMessage msg) {
        String path = msg.getAddressPattern().toString();
        if (QUERY.equals(path)) temporarilyDisableListeners();
        state.put(path, msg);
        boolean handled = lx.engine.handleOscMessage(msg, path.split("/"), 2);
        fire(path);
        LOG.debug("Forwarded INCOMING OSC, handled {}, msg: {}", handled, msg);
        if (!handled) throw new UnsupportedOperationException("Couldn't handle OSC message: " + msg);
    }

    public void sendMessage(String path, float data) {
        lx.engine.osc.sendMessage(path, data);
    }

    public void sendMessage(String path, int data) {
        lx.engine.osc.sendMessage(path, data);
    }

    private void temporarilyDisableListeners() {
        listeningToEvents = false;
        Orchestrator.schedule(() -> listeningToEvents = true, 500);
    }

    public void refresh() {
        command(QUERY);
    }

    private void wire() {
        // todo: Wish this did something, or there were some other hook to not have to chain Tx/Rx ?
        lx.engine.osc.addListener(msg -> LX.log("***** \n\n\n\n ***** Never works? OSC msg: " + msg));

        // If a client sends a message, we should handle it and treat it as a command like we'd do
        rxFromClients.addListener(this::command);

        // If LX is sending out [VALUABLE] state over OSC, store the last state, fire the event
        //   which will also use that last state (and trigger our event handlers), and, ofc, forward
        //   on to any clients
        rxFromLxLoopback.addListener(msg -> {
            LOG.debug("Forwarding OUTGOING OSC msg: {}", msg);
            String path = msg.getAddressPattern().toString();
            state.put(path, msg);
            fire(path);
            try {
                txToClients.send(msg);
            } catch (IOException e) {
                LX.error(e, "Error forwarding outgoing OSC message " + msg);
            }
        });
    }
}
