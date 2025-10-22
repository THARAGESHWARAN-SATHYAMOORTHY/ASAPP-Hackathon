import React, { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';
import './AdminPanel.css';

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('request-types');
  const [requestTypes, setRequestTypes] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingRequestType, setEditingRequestType] = useState(null);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'request-types') {
        const data = await adminAPI.getRequestTypes();
        setRequestTypes(data);
      } else if (activeTab === 'policies') {
        const data = await adminAPI.getPolicies();
        setPolicies(data);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRequestType = () => {
    setEditingRequestType({
      name: '',
      description: '',
      tasks: [
        {
          task_name: '',
          task_type: 'customer_input',
          execution_order: 1,
          configuration: {}
        }
      ]
    });
    setShowModal(true);
  };

  const handleEditRequestType = (requestType) => {
    setEditingRequestType(requestType);
    setShowModal(true);
  };

  const handleSaveRequestType = async () => {
    try {
      if (editingRequestType.id) {
        await adminAPI.updateRequestType(editingRequestType.id, editingRequestType);
      } else {
        await adminAPI.createRequestType(editingRequestType);
      }
      setShowModal(false);
      setEditingRequestType(null);
      loadData();
    } catch (error) {
      console.error('Error saving request type:', error);
      alert('Error saving request type');
    }
  };

  const handleDeleteRequestType = async (id) => {
    if (!confirm('Are you sure you want to deactivate this request type?')) return;
    
    try {
      await adminAPI.deleteRequestType(id);
      loadData();
    } catch (error) {
      console.error('Error deleting request type:', error);
    }
  };

  const handleInitializePolicies = async () => {
    try {
      await adminAPI.initializePolicies();
      loadData();
      alert('Policies initialized successfully!');
    } catch (error) {
      console.error('Error initializing policies:', error);
      alert('Error initializing policies');
    }
  };

  const addTask = () => {
    setEditingRequestType({
      ...editingRequestType,
      tasks: [
        ...editingRequestType.tasks,
        {
          task_name: '',
          task_type: 'customer_input',
          execution_order: editingRequestType.tasks.length + 1,
          configuration: {}
        }
      ]
    });
  };

  const removeTask = (index) => {
    const newTasks = editingRequestType.tasks.filter((_, i) => i !== index);
    // Reorder execution_order
    newTasks.forEach((task, i) => {
      task.execution_order = i + 1;
    });
    setEditingRequestType({
      ...editingRequestType,
      tasks: newTasks
    });
  };

  const updateTask = (index, field, value) => {
    const newTasks = [...editingRequestType.tasks];
    newTasks[index] = {
      ...newTasks[index],
      [field]: value
    };
    setEditingRequestType({
      ...editingRequestType,
      tasks: newTasks
    });
  };

  return (
    <div className="admin-panel">
      <div className="admin-container">
        <div className="admin-header">
          <h1>Admin Configuration Panel</h1>
          <p>Manage request types, tasks, and policies</p>
        </div>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'request-types' ? 'active' : ''}`}
            onClick={() => setActiveTab('request-types')}
          >
            Request Types
          </button>
          <button
            className={`tab ${activeTab === 'policies' ? 'active' : ''}`}
            onClick={() => setActiveTab('policies')}
          >
            Policies
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'request-types' && (
            <div className="request-types-section">
              <div className="section-header">
                <h2>Request Types Configuration</h2>
                <button className="btn-primary" onClick={handleCreateRequestType}>
                  + Create New Request Type
                </button>
              </div>

              {loading ? (
                <div className="loading">Loading...</div>
              ) : (
                <div className="request-types-grid">
                  {requestTypes.map((rt) => (
                    <div key={rt.id} className="request-type-card">
                      <div className="card-header">
                        <h3>{rt.name}</h3>
                        <div className="card-actions">
                          <button
                            className="btn-edit"
                            onClick={() => handleEditRequestType(rt)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn-delete"
                            onClick={() => handleDeleteRequestType(rt.id)}
                          >
                            Deactivate
                          </button>
                        </div>
                      </div>
                      <p className="card-description">{rt.description}</p>
                      <div className="tasks-list">
                        <strong>Tasks ({rt.tasks.length}):</strong>
                        <ol>
                          {rt.tasks.map((task) => (
                            <li key={task.id}>
                              <span className="task-name">{task.task_name}</span>
                              <span className="task-type">{task.task_type}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'policies' && (
            <div className="policies-section">
              <div className="section-header">
                <h2>Policy Documents</h2>
                <button className="btn-primary" onClick={handleInitializePolicies}>
                  Initialize Default Policies
                </button>
              </div>

              {loading ? (
                <div className="loading">Loading...</div>
              ) : (
                <div className="policies-grid">
                  {policies.map((policy) => (
                    <div key={policy.id} className="policy-card">
                      <div className="policy-type-badge">{policy.policy_type}</div>
                      <h3>{policy.title}</h3>
                      <p className="policy-content">{policy.content.substring(0, 200)}...</p>
                      {policy.source_url && (
                        <a href={policy.source_url} target="_blank" rel="noopener noreferrer" className="source-link">
                          View Source
                        </a>
                      )}
                      <div className="policy-meta">
                        Last updated: {new Date(policy.last_updated).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modal for editing request type */}
      {showModal && editingRequestType && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingRequestType.id ? 'Edit' : 'Create'} Request Type</h2>
              <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>Request Type Name</label>
                <input
                  type="text"
                  value={editingRequestType.name}
                  onChange={(e) => setEditingRequestType({
                    ...editingRequestType,
                    name: e.target.value
                  })}
                  placeholder="e.g., Cancel Trip"
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={editingRequestType.description || ''}
                  onChange={(e) => setEditingRequestType({
                    ...editingRequestType,
                    description: e.target.value
                  })}
                  placeholder="Describe what this request type handles"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <div className="tasks-header">
                  <label>Tasks</label>
                  <button className="btn-add-task" onClick={addTask}>+ Add Task</button>
                </div>

                <div className="tasks-editor">
                  {editingRequestType.tasks.map((task, index) => (
                    <div key={index} className="task-editor">
                      <div className="task-editor-header">
                        <span className="task-number">Task {index + 1}</span>
                        <button className="btn-remove" onClick={() => removeTask(index)}>
                          Remove
                        </button>
                      </div>

                      <div className="task-fields">
                        <div className="field">
                          <label>Task Name</label>
                          <input
                            type="text"
                            value={task.task_name}
                            onChange={(e) => updateTask(index, 'task_name', e.target.value)}
                            placeholder="e.g., Get flight details"
                          />
                        </div>

                        <div className="field">
                          <label>Task Type</label>
                          <select
                            value={task.task_type}
                            onChange={(e) => updateTask(index, 'task_type', e.target.value)}
                          >
                            <option value="customer_input">Customer Input</option>
                            <option value="api_call">API Call</option>
                            <option value="policy_lookup">Policy Lookup</option>
                            <option value="response">Response</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSaveRequestType}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;

