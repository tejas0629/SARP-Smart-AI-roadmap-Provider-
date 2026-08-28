export default function RoadmapPanel({ roadmap }) {
  if (!roadmap) {
    return (
      <aside className="roadmapCard empty">
        <div className="emptyIcon">🗺️</div>
        <h2>Your Personalized Learning Path</h2>
        <p>Tell me your learning goal in the chat and I'll create your roadmap.</p>
        <div className="hint">Try: “I want to become a Python Developer in 6 months.”</div>
      </aside>
    );
  }

  return (
    <aside className="roadmapCard">
      <div className="roadmapHero">
        <div className="heroIcon">🎯</div>
        <div>
          <p>Goal</p>
          <h2>{roadmap.goal || 'Personalized Learning Goal'}</h2>
          <span>{roadmap.duration || 'Flexible timeline'} · {roadmap.starting_level || 'Level not specified'}</span>
        </div>
      </div>
      <div className="timeline">
        {(roadmap.steps || []).map((step, index) => (
          <div className="timelineItem" key={`${step.title}-${index}`}>
            <div className="stepBadge">{index + 1}</div>
            <div className="stepCard">
              <div className="stepMeta">{step.duration || `Stage ${index + 1}`}</div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
              <ul>
                {(step.topics || []).map((topic) => <li key={topic}>{topic}</li>)}
              </ul>
            </div>
          </div>
        ))}
      </div>
      {!!roadmap.projects?.length && (
        <div className="miniSection">
          <h3>Projects</h3>
          {roadmap.projects.map((p) => <p key={p}>✅ {p}</p>)}
        </div>
      )}
      {roadmap.next_action && (
        <div className="nextAction"><strong>Next action:</strong> {roadmap.next_action}</div>
      )}
    </aside>
  );
}
