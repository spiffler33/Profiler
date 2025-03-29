/**
 * Data Event Bus Service
 * 
 * A simple pub/sub event bus for communicating between components.
 * This allows components to subscribe to data changes and publish events
 * without directly depending on each other.
 * 
 * Usage:
 * 1. Subscribe to events: DataEventBus.subscribe('probability-updated', callback)
 * 2. Publish events: DataEventBus.publish('probability-updated', { probability: 0.75 })
 * 3. Unsubscribe: DataEventBus.unsubscribe('probability-updated', callback)
 * 
 * ENHANCED: Added state synchronization and component coordination features
 */

const DataEventBus = (function() {
  // Private state
  const subscribers = {};
  const eventHistory = {};
  const activeComponents = new Set();
  const componentData = new Map();
  
  // Configuration
  const config = {
    maxHistoryLength: 10,
    debugMode: false,
    enableSync: true,
    syncInterval: 2000, // Sync check interval in ms
    allowedEvents: [
      'probability-updated',
      'adjustment-selected',
      'scenario-selected',
      'parameters-changed',
      'visualization-refreshed',
      'data-fetched',
      'component-mounted', // New event for component lifecycle
      'component-unmounted', // New event for component lifecycle
      'data-invalidated', // New event for cache invalidation
      'sync-requested' // New event for manual sync
    ]
  };

  // Interval ID for sync timer
  let syncIntervalId = null;

  /**
   * Initialize the event bus with active sync
   */
  function initialize() {
    if (config.enableSync) {
      startSyncProcess();
    }
    
    if (config.debugMode) {
      console.log('DataEventBus initialized with sync', config.enableSync ? 'enabled' : 'disabled');
    }
  }

  /**
   * Start the synchronization process
   */
  function startSyncProcess() {
    if (syncIntervalId) return; // Already running
    
    syncIntervalId = setInterval(() => {
      if (activeComponents.size > 1) {
        synchronizeComponents();
      }
    }, config.syncInterval);
    
    // Add window unload event to clean up
    window.addEventListener('beforeunload', () => {
      if (syncIntervalId) {
        clearInterval(syncIntervalId);
        syncIntervalId = null;
      }
    });
  }

  /**
   * Synchronize data between components
   */
  function synchronizeComponents() {
    if (config.debugMode) {
      console.log(`Synchronizing ${activeComponents.size} components`);
    }
    
    // Check if any component data has a more recent timestamp
    let latestData = {};
    let latestTimestamp = 0;
    
    // Find the latest data
    componentData.forEach((data, component) => {
      if (data.lastUpdated > latestTimestamp) {
        latestData = data;
        latestTimestamp = data.lastUpdated;
      }
    });
    
    // If we have latest data, broadcast to all other components
    if (latestTimestamp > 0) {
      const eventType = latestData.type || 'data-updated';
      
      // Only publish if the event type is allowed
      if (config.allowedEvents.includes(eventType)) {
        if (config.debugMode) {
          console.log(`Broadcasting ${eventType} data to all components from source: ${latestData.source}`);
        }
        
        publish(eventType, {
          ...latestData.payload,
          source: 'sync',
          syncSource: latestData.source,
          timestamp: Date.now()
        });
      }
    }
  }

  /**
   * Subscribe to an event
   * @param {string} eventName - Name of the event to subscribe to
   * @param {Function} callback - Function to call when event is published
   * @returns {Function} Unsubscribe function
   */
  function subscribe(eventName, callback) {
    if (typeof callback !== 'function') {
      console.error('Callback must be a function');
      return () => {};
    }

    // Validate event name
    if (config.allowedEvents.length > 0 && !config.allowedEvents.includes(eventName)) {
      console.warn(`Event "${eventName}" is not in the allowed events list`);
    }

    // Create subscribers array if it doesn't exist
    if (!subscribers[eventName]) {
      subscribers[eventName] = [];
    }

    // Add callback to subscribers
    subscribers[eventName].push(callback);

    // Log subscription in debug mode
    if (config.debugMode) {
      console.log(`Subscribed to event: ${eventName}`);
    }

    // Send the most recent event data if available
    if (eventHistory[eventName] && eventHistory[eventName].length > 0) {
      const latestEvent = eventHistory[eventName][eventHistory[eventName].length - 1];
      setTimeout(() => callback(latestEvent), 0);
    }

    // Return unsubscribe function
    return () => unsubscribe(eventName, callback);
  }

  /**
   * Unsubscribe from an event
   * @param {string} eventName - Name of the event to unsubscribe from
   * @param {Function} callback - Function to remove from subscribers
   */
  function unsubscribe(eventName, callback) {
    if (!subscribers[eventName]) return;

    // Filter out the callback
    subscribers[eventName] = subscribers[eventName].filter(cb => cb !== callback);

    // Log unsubscription in debug mode
    if (config.debugMode) {
      console.log(`Unsubscribed from event: ${eventName}`);
    }
  }

  /**
   * Publish an event
   * @param {string} eventName - Name of the event to publish
   * @param {any} data - Data to pass to subscribers
   */
  function publish(eventName, data) {
    // Validate event name
    if (config.allowedEvents.length > 0 && !config.allowedEvents.includes(eventName)) {
      console.warn(`Event "${eventName}" is not in the allowed events list`);
    }

    // Log publication in debug mode
    if (config.debugMode) {
      console.log(`Publishing event: ${eventName}`, data);
    }

    // Add timestamp to data
    const eventData = {
      ...data,
      timestamp: new Date().getTime()
    };

    // Store in history
    if (!eventHistory[eventName]) {
      eventHistory[eventName] = [];
    }
    eventHistory[eventName].push(eventData);

    // Limit history length
    if (eventHistory[eventName].length > config.maxHistoryLength) {
      eventHistory[eventName] = eventHistory[eventName].slice(-config.maxHistoryLength);
    }

    // If no subscribers, log in debug mode and return
    if (!subscribers[eventName] || subscribers[eventName].length === 0) {
      if (config.debugMode) {
        console.log(`No subscribers for event: ${eventName}`);
      }
      return;
    }

    // Notify all subscribers
    subscribers[eventName].forEach(callback => {
      try {
        callback(eventData);
      } catch (error) {
        console.error(`Error in subscriber to ${eventName}:`, error);
      }
    });
  }

  /**
   * Get the last published data for an event
   * @param {string} eventName - Name of the event
   * @returns {any|null} Last published data or null if none
   */
  function getLastEvent(eventName) {
    if (!eventHistory[eventName] || eventHistory[eventName].length === 0) {
      return null;
    }
    return eventHistory[eventName][eventHistory[eventName].length - 1];
  }

  /**
   * Clear all subscribers and history for an event
   * @param {string} eventName - Name of the event to clear
   */
  function clearEvent(eventName) {
    delete subscribers[eventName];
    delete eventHistory[eventName];

    if (config.debugMode) {
      console.log(`Cleared event: ${eventName}`);
    }
  }

  /**
   * Clear all subscribers and history
   */
  function clearAll() {
    Object.keys(subscribers).forEach(clearEvent);
    
    if (config.debugMode) {
      console.log('Cleared all events');
    }
  }

  /**
   * Configure the event bus
   * @param {Object} options - Configuration options
   */
  function configure(options = {}) {
    Object.assign(config, options);
    
    // Update sync interval if running
    if (syncIntervalId && options.syncInterval) {
      clearInterval(syncIntervalId);
      syncIntervalId = setInterval(() => {
        if (activeComponents.size > 1) {
          synchronizeComponents();
        }
      }, config.syncInterval);
    }
  }
  
  /**
   * Register a component with the event bus
   * @param {string} componentId - Unique identifier for the component
   * @param {string} componentType - Type of component (e.g., 'visualizer', 'adjustmentPanel')
   * @param {Object} initialData - Initial data for the component
   */
  function registerComponent(componentId, componentType, initialData = {}) {
    activeComponents.add(componentId);
    
    componentData.set(componentId, {
      type: componentType,
      lastUpdated: Date.now(),
      payload: initialData,
      source: componentId
    });
    
    // Publish component mounted event
    publish('component-mounted', {
      componentId,
      componentType,
      initialData,
      source: componentId
    });
    
    if (config.debugMode) {
      console.log(`Component registered: ${componentId} (${componentType})`);
      console.log(`Active components: ${activeComponents.size}`);
    }
    
    // Return unregister function
    return () => unregisterComponent(componentId);
  }
  
  /**
   * Unregister a component from the event bus
   * @param {string} componentId - Unique identifier for the component
   */
  function unregisterComponent(componentId) {
    activeComponents.delete(componentId);
    componentData.delete(componentId);
    
    // Publish component unmounted event
    publish('component-unmounted', {
      componentId,
      source: 'system'
    });
    
    if (config.debugMode) {
      console.log(`Component unregistered: ${componentId}`);
      console.log(`Active components: ${activeComponents.size}`);
    }
  }
  
  /**
   * Update component data
   * @param {string} componentId - Unique identifier for the component
   * @param {string} eventType - Type of event that triggered the update
   * @param {Object} data - New data for the component
   */
  function updateComponentData(componentId, eventType, data) {
    if (!activeComponents.has(componentId)) {
      if (config.debugMode) {
        console.warn(`Attempting to update data for unregistered component: ${componentId}`);
      }
      return;
    }
    
    componentData.set(componentId, {
      type: eventType,
      lastUpdated: Date.now(),
      payload: data,
      source: componentId
    });
    
    if (config.debugMode) {
      console.log(`Component data updated: ${componentId} (${eventType})`);
    }
  }
  
  /**
   * Force synchronization of components
   */
  function forceSynchronization() {
    synchronizeComponents();
    
    // Broadcast sync event
    publish('sync-requested', {
      source: 'manual',
      timestamp: Date.now()
    });
  }
  
  /**
   * Get list of active components
   * @returns {Array} Array of active component IDs
   */
  function getActiveComponents() {
    return Array.from(activeComponents);
  }

  // Initialize on load
  initialize();

  // Public API
  return {
    subscribe,
    unsubscribe,
    publish,
    getLastEvent,
    clearEvent,
    clearAll,
    configure,
    registerComponent,
    unregisterComponent,
    updateComponentData,
    forceSynchronization,
    getActiveComponents
  };
})();

// Make available globally
window.DataEventBus = DataEventBus;