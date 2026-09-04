"use client";

import { useEffect, useState } from "react";

type Project = { id: string; name: string };

export default function Page() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [visibleProjects, setVisibleProjects] = useState<Project[]>([]);

  useEffect(() => {
    fetch("/api/projects")
      .then((response) => response.json())
      .then((data: Project[]) => {
        setProjects(data);
        setVisibleProjects(data);
      });
  }, []);

  return (
    <main>
      <h1>Projects</h1>
      {visibleProjects.map((project) => (
        <div key={project.id} onClick={() => setVisibleProjects(projects.filter((item) => item.id !== project.id))}>
          {project.name}
        </div>
      ))}
    </main>
  );
}
