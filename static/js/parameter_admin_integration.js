/**
 * parameter_admin_integration.js
 * 
 * This script integrates the ParameterAdminService with the existing parameter
 * management interface in the application. It handles the connection between the
 * API-based parameter management and the UI components.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Check if we're on the parameter admin page
  const parametersGrid = document.getElementById('parameters-grid');
  if (!parametersGrid) return;
  
  // Check if API services are loaded
  const hasApiService = typeof ApiService !== 'undefined';
  const hasParameterAdminService = typeof ParameterAdminService !== 'undefined';
  
  if (!hasApiService) {
    console.warn('ApiService not found. Parameters Admin API integration will be limited.');
  }
  
  if (!hasParameterAdminService) {
    console.warn('ParameterAdminService not found. Parameters Admin API integration will be limited.');
  }
  
  // Initialize the ParameterAdminService if available
  if (hasParameterAdminService) {
    ParameterAdminService.initialize({ cacheTTL: 5 * 60 * 1000 }); // 5 minute cache
  }
  
  // Override existing data loading functions with API integration
  if (hasParameterAdminService) {
    // Replace loadParameters function
    window.loadParameters = function() {
      ParameterAdminService.getParameters({ forceRefresh: true })
        .then(data => {
          allParameters = data.parameters;
          parameterTree = data.tree;
          
          // Update UI
          renderParameterGrid(allParameters);
          renderParameterTree(parameterTree);
          loadAuditLog();
        })
        .catch(error => {
          console.error('Error loading parameters:', error);
          document.getElementById('parameters-grid').innerHTML = 
            '<div class="col-12"><div class="alert alert-danger">Error loading parameters. Please try again.</div></div>';
        });
    };
    
    // Replace loadProfiles function
    window.loadProfiles = function() {
      ParameterAdminService.getProfiles()
        .then(data => {
          allProfiles = data;
          const selector = document.getElementById('profileSelector');
          
          // Clear existing options
          selector.innerHTML = '<option value="">Select a profile</option>';
          
          // Add profiles
          data.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.name;
            selector.appendChild(option);
          });
        })
        .catch(error => {
          console.error('Error loading profiles:', error);
        });
    };
    
    // Replace loadUserParameters function
    window.loadUserParameters = function(profileId) {
      ParameterAdminService.getUserParameters(profileId)
        .then(data => {
          renderUserParameters(data, profileId);
        })
        .catch(error => {
          console.error('Error loading user parameters:', error);
          document.getElementById('user-parameters').innerHTML = 
            '<div class="alert alert-danger">Error loading user parameter overrides. Please try again.</div>';
        });
    };
    
    // Replace loadAuditLog function
    window.loadAuditLog = function() {
      const searchTerm = document.getElementById('auditSearch')?.value || '';
      const actionFilter = document.getElementById('auditActionFilter')?.value || '';
      
      ParameterAdminService.getAuditLog({
        search: searchTerm,
        action: actionFilter,
        forceRefresh: !searchTerm && !actionFilter // Only force refresh for unfiltered queries
      })
        .then(data => {
          renderAuditLog(data);
        })
        .catch(error => {
          console.error('Error loading audit log:', error);
          document.getElementById('audit-log').innerHTML = 
            '<div class="alert alert-danger">Error loading audit log. Please try again.</div>';
        });
    };
    
    // Replace filterAuditLog function
    window.filterAuditLog = function() {
      loadAuditLog(); // Use the updated loadAuditLog function
    };
    
    // Override parameter detail functions
    window.showParameterDetails = function(parameter) {
      selectedParameter = parameter;
      
      // Populate detail modal
      document.getElementById('detail-path').textContent = parameter.path;
      document.getElementById('detail-value').textContent = formatParameterValue(parameter.value);
      document.getElementById('detail-type').textContent = typeof parameter.value;
      document.getElementById('detail-source').textContent = parameter.source || 'system';
      document.getElementById('detail-description').textContent = parameter.description || 'No description available';
      document.getElementById('detail-updated').textContent = parameter.last_updated ? formatDate(parameter.last_updated) : 'Unknown';
      document.getElementById('detail-created').textContent = parameter.created ? formatDate(parameter.created) : 'Unknown';
      
      // Update the documentation panel
      updateDocumentationPanel(parameter);
      
      // Find related parameters using the API
      ParameterAdminService.getRelatedParameters(parameter.path)
        .then(data => {
          renderRelatedParameters(data);
        })
        .catch(error => {
          console.error('Error loading related parameters:', error);
          document.getElementById('related-parameters').innerHTML = 
            '<p class="text-muted">Failed to load related parameters</p>';
        });
      
      // Show modal
      $('#parameterDetailModal').modal('show');
    };
    
    // Override editParameter function
    window.editParameter = function(parameter) {
      document.getElementById('editParameterPath').value = parameter.path;
      document.getElementById('editParameterDisplay').value = parameter.path;
      document.getElementById('editParameterValue').value = parameter.value;
      document.getElementById('editParameterDescription').value = parameter.description || '';
      document.getElementById('editParameterSource').value = parameter.source || 'admin';
      document.getElementById('editParameterIsEditable').checked = parameter.is_editable !== false;
      
      // Load parameter history using the API
      ParameterAdminService.getParameterHistory(parameter.path)
        .then(data => {
          renderParameterHistory(data);
        })
        .catch(error => {
          console.error('Error loading parameter history:', error);
          document.getElementById('parameter-history').innerHTML = '<p class="text-muted">Failed to load history</p>';
        });
      
      // Show modal
      $('#editParameterModal').modal('show');
    };
    
    // Override saveParameter function
    window.saveParameter = function() {
      const path = document.getElementById('parameterPath').value;
      const value = document.getElementById('parameterValue').value;
      const description = document.getElementById('parameterDescription').value;
      const source = document.getElementById('parameterSource').value;
      const isEditable = document.getElementById('parameterIsEditable').checked;
      
      if (!path || !value) {
        alert('Parameter path and value are required');
        return;
      }
      
      const paramData = {
        path,
        value,
        description,
        source,
        is_editable: isEditable
      };
      
      ParameterAdminService.createParameter(paramData)
        .then(data => {
          if (data.success) {
            $('#addParameterModal').modal('hide');
            document.getElementById('addParameterForm').reset();
            loadParameters();
          } else {
            alert('Failed to save parameter: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(error => {
          console.error('Error saving parameter:', error);
          alert('An error occurred while saving the parameter.');
        });
    };
    
    // Override updateParameter function
    window.updateParameter = function() {
      const path = document.getElementById('editParameterPath').value;
      const value = document.getElementById('editParameterValue').value;
      const description = document.getElementById('editParameterDescription').value;
      const source = document.getElementById('editParameterSource').value;
      const isEditable = document.getElementById('editParameterIsEditable').checked;
      
      if (!path || !value) {
        alert('Parameter path and value are required');
        return;
      }
      
      const paramData = {
        value,
        description,
        source,
        is_editable: isEditable
      };
      
      ParameterAdminService.updateParameter(path, paramData)
        .then(data => {
          if (data.success) {
            $('#editParameterModal').modal('hide');
            loadParameters();
          } else {
            alert('Failed to update parameter: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(error => {
          console.error('Error updating parameter:', error);
          alert('An error occurred while updating the parameter.');
        });
    };
    
    // Override deleteParameter function
    window.deleteParameter = function() {
      const path = document.getElementById('editParameterPath').value;
      
      if (!confirm(`Are you sure you want to delete the parameter: ${path}? This action cannot be undone.`)) {
        return;
      }
      
      ParameterAdminService.deleteParameter(path)
        .then(data => {
          if (data.success) {
            $('#editParameterModal').modal('hide');
            loadParameters();
          } else {
            alert('Failed to delete parameter: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(error => {
          console.error('Error deleting parameter:', error);
          alert('An error occurred while deleting the parameter.');
        });
    };
    
    // Override user parameter functions
    window.updateUserOverride = function(profileId, path, value) {
      ParameterAdminService.updateUserParameter(profileId, path, value)
        .then(data => {
          if (data.success) {
            loadUserParameters(profileId);
          } else {
            alert('Failed to update parameter override: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(error => {
          console.error('Error updating user parameter:', error);
          alert('An error occurred while updating the parameter override.');
        });
    };
    
    window.resetUserOverride = function(profileId, path) {
      if (!confirm(`Reset the override for ${path} to global value?`)) {
        return;
      }
      
      ParameterAdminService.resetUserParameter(profileId, path)
        .then(data => {
          if (data.success) {
            loadUserParameters(profileId);
          } else {
            alert('Failed to reset parameter override: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(error => {
          console.error('Error resetting user parameter:', error);
          alert('An error occurred while resetting the parameter override.');
        });
    };
  }
  
  // Update the documentation panel with impact information
  window.updateDocumentationPanel = function(parameter) {
    const panel = document.getElementById('parameter-documentation');
    
    panel.innerHTML = `
      <h4 class="mb-3">${getParameterName(parameter.path)}</h4>
      <p class="parameter-path mb-4">${parameter.path}</p>
      
      <div class="mb-4">
        <h5>Current Value</h5>
        <div class="p-3 bg-light rounded">
          <span class="badge bg-secondary me-2">${typeof parameter.value}</span>
          <span>${formatParameterValue(parameter.value)}</span>
        </div>
      </div>
      
      <div class="mb-4">
        <h5>Description</h5>
        <p>${parameter.description || 'No description available for this parameter.'}</p>
      </div>
      
      <div class="mb-4">
        <h5>Impact & Usage</h5>
        <p>This parameter affects the following calculations:</p>
        <ul id="impact-list">
          <li>Loading impact information...</li>
        </ul>
      </div>
      
      <div class="mb-4">
        <h5>Historical Values</h5>
        <div id="history-chart" style="height: 200px;">
          <!-- Chart will be rendered here -->
        </div>
      </div>
      
      <div class="mb-4">
        <h5>Metadata</h5>
        <table class="table table-sm">
          <tr>
            <td>Source</td>
            <td>${parameter.source || 'system'}</td>
          </tr>
          <tr>
            <td>Last Updated</td>
            <td>${parameter.last_updated ? formatDate(parameter.last_updated) : 'Unknown'}</td>
          </tr>
          <tr>
            <td>Created</td>
            <td>${parameter.created ? formatDate(parameter.created) : 'Unknown'}</td>
          </tr>
          <tr>
            <td>User Editable</td>
            <td>${parameter.is_editable !== false ? 'Yes' : 'No'}</td>
          </tr>
        </table>
      </div>
    `;
    
    // Load impact information using the API
    if (hasParameterAdminService) {
      ParameterAdminService.getParameterImpact(parameter.path)
        .then(data => {
          renderParameterImpact(data);
        })
        .catch(error => {
          console.error('Error loading parameter impact:', error);
          document.getElementById('impact-list').innerHTML = 
            '<li>Unable to load impact information</li>';
        });
    } else {
      // Use the original fetch-based approach
      fetch(`/api/admin/parameters/impact/${encodeURIComponent(parameter.path)}`)
        .then(response => response.json())
        .then(data => {
          renderParameterImpact(data);
        })
        .catch(error => {
          console.error('Error loading parameter impact:', error);
          document.getElementById('impact-list').innerHTML = 
            '<li>Unable to load impact information</li>';
        });
    }
  };
  
  // Set up loading state integration with LoadingStateManager
  if (window.LoadingStateManager) {
    window.addEventListener('parameterAdminLoading', function(event) {
      const { id, isLoading } = event.detail;
      LoadingStateManager.setLoading(`parameter-admin-${id}`, isLoading, {
        text: `${isLoading ? 'Loading' : 'Loaded'} ${id}...`
      });
    });
  }
  
  // Set up error handling integration with ErrorHandlingService
  if (window.ErrorHandlingService) {
    window.addEventListener('parameterAdminError', function(event) {
      const { error, context } = event.detail;
      ErrorHandlingService.handleError(error, 'parameter_admin', {
        showToast: true,
        metadata: { context }
      });
    });
  }
  
  // Initialize data loading
  if (window.loadParameters) {
    window.loadParameters();
  }
  
  if (window.loadProfiles) {
    window.loadProfiles();
  }
  
  console.log('Parameter Admin API integration initialized successfully');
});