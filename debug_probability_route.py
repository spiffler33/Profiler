@app.route('/check_probability/<goal_id>')
def check_probability(goal_id):
    """Debug route to check probability display for a specific goal"""
    goal_service = app.config.get('goal_service', GoalService())
    goal = goal_service.get_goal(goal_id)
    if not goal:
        return "Goal not found", 404
    return render_template('check_probability.html', goal=goal)

@app.route('/update_probability/<goal_id>', methods=['POST'])
def update_probability(goal_id):
    """Update a goal's probability for testing display"""
    try:
        goal_service = app.config.get('goal_service', GoalService())
        new_prob = request.form.get('new_prob')
        
        # Convert to float and validate
        try:
            new_prob_value = float(new_prob)
        except (ValueError, TypeError):
            return "Invalid probability value", 400
            
        # Update the probability
        result = goal_service.update_goal_probability(goal_id, new_prob_value)
        
        if result:
            flash("Probability updated successfully", "success")
        else:
            flash("Failed to update probability", "error")
            
        return redirect(url_for('check_probability', goal_id=goal_id))
    except Exception as e:
        return f"Error: {str(e)}", 500
