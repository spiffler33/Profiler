/**
 * API integration hooks and HOCs for React components
 * 
 * This module provides React hooks and higher-order components (HOCs) for
 * consistent API integration across components. These utilities simplify
 * data fetching, error handling, loading states, and more.
 */

/**
 * React hook for fetching API data
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Request options
 * @returns {Object} { data, loading, error, refetch }
 */
function useApiData(endpoint, options = {}) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [refetchCount, setRefetchCount] = React.useState(0);
  
  // Dependencies to watch for refetching
  const dependencies = options.dependencies || [];
  
  // Function to trigger data refetch
  const refetch = React.useCallback(() => {
    setRefetchCount(prev => prev + 1);
  }, []);
  
  React.useEffect(() => {
    // Skip if endpoint is not provided
    if (!endpoint) {
      setLoading(false);
      return;
    }
    
    let isMounted = true;
    setLoading(true);
    
    const fetchData = async () => {
      try {
        // Use the loadingId from options or generate one
        const apiOptions = {
          ...options,
          loadingId: options.loadingId || `fetch-${endpoint.replace(/\W/g, '-')}`
        };
        
        const result = await window.ApiService.get(endpoint, apiOptions);
        
        if (isMounted) {
          setData(result);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err);
          setData(null);
          setLoading(false);
        }
      }
    };
    
    fetchData();
    
    // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [endpoint, refetchCount, ...dependencies]);
  
  return { data, loading, error, refetch };
}

/**
 * React hook for submitting data to API
 * @param {string} endpoint - API endpoint
 * @param {string} method - HTTP method (POST, PUT, etc.)
 * @param {Object} options - Request options
 * @returns {Object} { submit, loading, error, data, reset }
 */
function useApiSubmit(endpoint, method = 'POST', options = {}) {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [data, setData] = React.useState(null);
  
  // Reset the state
  const reset = React.useCallback(() => {
    setError(null);
    setData(null);
  }, []);
  
  // Submit function
  const submit = React.useCallback(async (formData) => {
    if (!endpoint) {
      throw new Error('Endpoint is required for submission');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Use the loadingId from options or generate one
      const apiOptions = {
        ...options,
        loadingId: options.loadingId || `submit-${endpoint.replace(/\W/g, '-')}`
      };
      
      let result;
      
      // Use the appropriate method
      if (method === 'POST') {
        result = await window.ApiService.post(endpoint, formData, apiOptions);
      } else if (method === 'PUT') {
        result = await window.ApiService.put(endpoint, formData, apiOptions);
      } else if (method === 'DELETE') {
        result = await window.ApiService.delete(endpoint, apiOptions);
      } else {
        // For other methods, use the request method directly
        result = await window.ApiService.request(method, endpoint, formData, apiOptions);
      }
      
      setData(result);
      setLoading(false);
      return result;
    } catch (err) {
      setError(err);
      setLoading(false);
      throw err;
    }
  }, [endpoint, method, options]);
  
  return { submit, loading, error, data, reset };
}

/**
 * React hook for API polling (for real-time updates)
 * @param {string} endpoint - API endpoint
 * @param {number} interval - Polling interval in ms
 * @param {Object} options - Request options
 * @returns {Object} { data, loading, error, startPolling, stopPolling }
 */
function useApiPolling(endpoint, interval = 5000, options = {}) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [isPolling, setIsPolling] = React.useState(options.autoStart !== false);
  
  // Store interval ID in a ref to prevent it from being included in dependency arrays
  const intervalRef = React.useRef(null);
  
  // Function to fetch data
  const fetchData = React.useCallback(async () => {
    if (!endpoint) return;
    
    try {
      // Use the loadingId from options or generate one for the first load
      const apiOptions = {
        ...options,
        loadingId: !data && (options.loadingId || `poll-${endpoint.replace(/\W/g, '-')}`)
      };
      
      const result = await window.ApiService.get(endpoint, apiOptions);
      setData(result);
      setError(null);
      setLoading(false);
    } catch (err) {
      setError(err);
      setLoading(false);
      
      // Stop polling on critical errors if configured
      if (options.stopOnError) {
        stopPolling();
      }
    }
  }, [endpoint, options]);
  
  // Start polling function
  const startPolling = React.useCallback(() => {
    setIsPolling(true);
  }, []);
  
  // Stop polling function
  const stopPolling = React.useCallback(() => {
    setIsPolling(false);
  }, []);
  
  // Setup polling
  React.useEffect(() => {
    // Skip if not polling or no endpoint
    if (!isPolling || !endpoint) {
      return;
    }
    
    // Fetch immediately
    fetchData();
    
    // Setup polling interval
    intervalRef.current = setInterval(fetchData, interval);
    
    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [endpoint, interval, isPolling, fetchData]);
  
  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, []);
  
  return { data, loading, error, startPolling, stopPolling, isPolling };
}

/**
 * React hook for API-powered forms
 * @param {Object} initialValues - Initial form values
 * @param {Function} onSubmit - Function to call on submission
 * @param {Object} options - Form options
 * @returns {Object} Form state and handlers
 */
function useApiForm(initialValues = {}, onSubmit, options = {}) {
  const [values, setValues] = React.useState(initialValues);
  const [touched, setTouched] = React.useState({});
  const [errors, setErrors] = React.useState({});
  const [submitting, setSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState(null);
  const [submitted, setSubmitted] = React.useState(false);
  
  // Update initial values if they change
  React.useEffect(() => {
    if (options.resetOnInitialChange) {
      setValues(initialValues);
      setTouched({});
      setErrors({});
      setSubmitted(false);
      setSubmitError(null);
    }
  }, [initialValues, options.resetOnInitialChange]);
  
  // Validation function
  const validate = React.useCallback((formValues = values) => {
    if (!options.validate) return {};
    return options.validate(formValues);
  }, [values, options]);
  
  // Run validation when values change if validateOnChange is true
  React.useEffect(() => {
    if (options.validateOnChange) {
      setErrors(validate());
    }
  }, [values, options.validateOnChange, validate]);
  
  // Handle input change
  const handleChange = React.useCallback((e) => {
    const { name, value, type, checked } = e.target;
    
    // Handle different input types
    const inputValue = type === 'checkbox' ? checked : value;
    
    setValues(prev => ({
      ...prev,
      [name]: inputValue
    }));
    
    // Mark as touched
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));
    
    // Validate if validateOnChange is true
    if (options.validateOnChange) {
      setErrors(validate({
        ...values,
        [name]: inputValue
      }));
    }
  }, [values, validate, options.validateOnChange]);
  
  // Handle blur event
  const handleBlur = React.useCallback((e) => {
    const { name } = e.target;
    
    // Mark as touched
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));
    
    // Validate if validateOnBlur is true
    if (options.validateOnBlur) {
      setErrors(validate());
    }
  }, [validate, options.validateOnBlur]);
  
  // Reset form
  const resetForm = React.useCallback(() => {
    setValues(initialValues);
    setTouched({});
    setErrors({});
    setSubmitted(false);
    setSubmitError(null);
  }, [initialValues]);
  
  // Set field value programmatically
  const setFieldValue = React.useCallback((name, value) => {
    setValues(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);
  
  // Set multiple field values programmatically
  const setFieldValues = React.useCallback((newValues) => {
    setValues(prev => ({
      ...prev,
      ...newValues
    }));
  }, []);
  
  // Handle form submission
  const handleSubmit = React.useCallback(async (e) => {
    if (e) e.preventDefault();
    
    // Validate all fields
    const validationErrors = validate();
    setErrors(validationErrors);
    
    // Mark all fields as touched
    const allTouched = Object.keys(values).reduce((acc, key) => {
      acc[key] = true;
      return acc;
    }, {});
    setTouched(allTouched);
    
    // Check if there are any errors
    const hasErrors = Object.keys(validationErrors).length > 0;
    if (hasErrors) {
      return;
    }
    
    // If there's no submit handler, return
    if (!onSubmit) {
      return;
    }
    
    setSubmitting(true);
    setSubmitError(null);
    
    try {
      await onSubmit(values);
      setSubmitted(true);
      
      // Reset if configured
      if (options.resetOnSubmit) {
        resetForm();
      }
    } catch (error) {
      setSubmitError(error);
      
      // Handle API error mapping if configured
      if (options.mapApiErrors && error.data) {
        const apiErrors = options.mapApiErrors(error.data);
        setErrors(prev => ({
          ...prev,
          ...apiErrors
        }));
      }
    } finally {
      setSubmitting(false);
    }
  }, [values, onSubmit, validate, options, resetForm]);
  
  return {
    values,
    touched,
    errors,
    handleChange,
    handleBlur,
    handleSubmit,
    resetForm,
    setFieldValue,
    setFieldValues,
    submitting,
    submitted,
    submitError,
    isValid: Object.keys(errors).length === 0
  };
}

/**
 * HOC that connects a component to API data
 * @param {React.Component} WrappedComponent - Component to wrap
 * @param {string|Function} endpointGetter - API endpoint or function to get endpoint from props
 * @param {Object} options - Connection options
 * @returns {React.Component} Connected component
 */
function withApiData(WrappedComponent, endpointGetter, options = {}) {
  function WithApiData(props) {
    // Get the endpoint (either directly or from a function)
    const endpoint = typeof endpointGetter === 'function' 
      ? endpointGetter(props) 
      : endpointGetter;
    
    // Use the hook to manage data fetching
    const { data, loading, error, refetch } = useApiData(
      endpoint,
      options
    );
    
    // Pass props to wrapped component
    return (
      <WrappedComponent
        {...props}
        apiData={data}
        apiLoading={loading}
        apiError={error}
        refetchApiData={refetch}
      />
    );
  }
  
  // Set display name for debugging
  WithApiData.displayName = `withApiData(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;
  
  return WithApiData;
}

/**
 * HOC that adds API submission capabilities to a component
 * @param {React.Component} WrappedComponent - Component to wrap
 * @param {string|Function} endpointGetter - API endpoint or function to get endpoint from props
 * @param {string} method - HTTP method
 * @param {Object} options - Connection options
 * @returns {React.Component} Connected component
 */
function withApiSubmit(WrappedComponent, endpointGetter, method = 'POST', options = {}) {
  function WithApiSubmit(props) {
    // Get the endpoint (either directly or from a function)
    const endpoint = typeof endpointGetter === 'function' 
      ? endpointGetter(props) 
      : endpointGetter;
    
    // Use the hook to manage submission
    const { submit, loading, error, data, reset } = useApiSubmit(
      endpoint,
      method,
      options
    );
    
    // Pass props to wrapped component
    return (
      <WrappedComponent
        {...props}
        apiSubmit={submit}
        apiSubmitLoading={loading}
        apiSubmitError={error}
        apiSubmitData={data}
        resetApiSubmit={reset}
      />
    );
  }
  
  // Set display name for debugging
  WithApiSubmit.displayName = `withApiSubmit(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;
  
  return WithApiSubmit;
}

/**
 * Adapter for connecting non-React components to the API
 */
const ApiConnectionAdapter = {
  /**
   * Connect a non-React component to the API
   * @param {Object} component - Component to connect
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Connection options
   */
  connect(component, endpoint, options = {}) {
    if (!component || !endpoint) {
      console.error('Component and endpoint are required for API connection');
      return null;
    }
    
    const {
      loadingCallback,
      dataCallback,
      errorCallback,
      autoLoad = true,
      method = 'GET',
      data = null,
      transformData = data => data
    } = options;
    
    // Create a unique ID for this connection
    const connectionId = `connection-${Math.random().toString(36).substring(2, 9)}`;
    
    // Register component with event bus if available
    let unregister = null;
    if (window.DataEventBus) {
      unregister = window.DataEventBus.registerComponent(
        connectionId,
        'api-connected',
        { endpoint }
      );
    }
    
    // Function to load data
    const loadData = async () => {
      if (loadingCallback) {
        loadingCallback(true);
      }
      
      try {
        let result;
        
        if (method === 'GET') {
          result = await window.ApiService.get(endpoint, options);
        } else if (method === 'POST') {
          result = await window.ApiService.post(endpoint, data, options);
        } else if (method === 'PUT') {
          result = await window.ApiService.put(endpoint, data, options);
        } else if (method === 'DELETE') {
          result = await window.ApiService.delete(endpoint, options);
        } else {
          result = await window.ApiService.request(method, endpoint, data, options);
        }
        
        // Transform data if specified
        const transformedData = transformData ? transformData(result) : result;
        
        if (dataCallback) {
          dataCallback(transformedData);
        }
        
        // Publish to event bus if available
        if (window.DataEventBus) {
          window.DataEventBus.publish('data-fetched', {
            endpoint,
            source: connectionId,
            data: transformedData
          });
        }
        
        return transformedData;
      } catch (error) {
        if (errorCallback) {
          errorCallback(error);
        }
        throw error;
      } finally {
        if (loadingCallback) {
          loadingCallback(false);
        }
      }
    };
    
    // Auto-load if specified
    if (autoLoad) {
      loadData();
    }
    
    // Return controller
    return {
      load: loadData,
      disconnect: () => {
        if (unregister) {
          unregister();
        }
      }
    };
  },
  
  /**
   * Create a subscription to an API endpoint with automatic polling
   * @param {string} endpoint - API endpoint
   * @param {number} interval - Polling interval in ms
   * @param {Object} options - Connection options
   * @returns {Object} Subscription controller
   */
  createSubscription(endpoint, interval = 5000, options = {}) {
    const {
      onData,
      onError,
      onStatusChange,
      autoStart = true,
      transformData = data => data
    } = options;
    
    let intervalId = null;
    let isActive = false;
    
    // Function to fetch data
    const fetchData = async () => {
      if (!isActive) return;
      
      try {
        const result = await window.ApiService.get(endpoint, options);
        const transformedData = transformData ? transformData(result) : result;
        
        if (onData) {
          onData(transformedData);
        }
        
        return transformedData;
      } catch (error) {
        if (onError) {
          onError(error);
        }
        
        // Stop polling on critical errors if configured
        if (options.stopOnError) {
          stop();
        }
      }
    };
    
    // Function to start subscription
    const start = () => {
      if (isActive) return;
      
      isActive = true;
      
      if (onStatusChange) {
        onStatusChange(true);
      }
      
      // Fetch immediately
      fetchData();
      
      // Setup polling
      intervalId = setInterval(fetchData, interval);
    };
    
    // Function to stop subscription
    const stop = () => {
      if (!isActive) return;
      
      isActive = false;
      
      if (onStatusChange) {
        onStatusChange(false);
      }
      
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };
    
    // Auto-start if configured
    if (autoStart) {
      start();
    }
    
    // Return controller
    return {
      start,
      stop,
      isActive: () => isActive,
      fetchNow: fetchData,
      setInterval: (newInterval) => {
        interval = newInterval;
        
        // Restart if active
        if (isActive) {
          stop();
          start();
        }
      }
    };
  }
};

// Export as window.ApiHooks to make available globally
window.ApiHooks = {
  useApiData,
  useApiSubmit,
  useApiPolling,
  useApiForm,
  withApiData,
  withApiSubmit,
  ApiConnectionAdapter
};