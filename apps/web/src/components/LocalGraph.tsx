"use client";
import { PageNode } from "@/api";
import { useEffect, useRef } from "react";

interface Props {
  node: PageNode;
  neighbors: PageNode[];
}

export function LocalGraph({ node, neighbors }: Props) {
  // Other state and event handling can go here
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate the center of the canvas
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Draw the current node in the center
    ctx.fillStyle = "blue";
    ctx.beginPath();
    ctx.arc(centerX, centerY, 20, 0, 2 * Math.PI);
    ctx.fill();
    ctx.fillStyle = "white";
    ctx.fillText(node.title, centerX - 15, centerY);

    // Draw immediate neighbors around the current node
    const radius = 100;
    const angleStep = (2 * Math.PI) / neighbors.length;

    neighbors.forEach((neighbor, index) => {
      const angle = index * angleStep;
      const neighborX = centerX + radius * Math.cos(angle);
      const neighborY = centerY + radius * Math.sin(angle);

      // Draw a node
      ctx.fillStyle = "green";
      ctx.beginPath();
      ctx.arc(neighborX, neighborY, 20, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = "white";
      ctx.fillText(neighbor.title, neighborX - 15, neighborY);

      // Draw a line connecting the current node to its neighbor
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(neighborX, neighborY);
      ctx.stroke();
    });
  }, [node, neighbors]);

  return (
    <canvas
      ref={canvasRef}
      width={800} // Set the canvas size as needed
      height={800}
    />
  );
}
