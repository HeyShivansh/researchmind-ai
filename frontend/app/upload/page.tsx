"use client";

import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
  Brain,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/common";
import { uploadApi } from "@/services/upload";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import type { PaperUploadResponse } from "@/types";

// =============================================================================
// Upload Page
// =============================================================================

const ACCEPTED_TYPES = ["application/pdf"];
const MAX_SIZE_MB = 50;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

type UploadStatus = "idle" | "dragging" | "uploading" | "success" | "error";

interface UploadItem {
  file: File;
  progress: number;
  status: UploadStatus;
  response?: PaperUploadResponse;
  error?: string;
}

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [title, setTitle] = useState("");

  const addFiles = (files: FileList | File[]) => {
    const newItems: UploadItem[] = [];
    for (const file of Array.from(files)) {
      // Validate
      if (!ACCEPTED_TYPES.includes(file.type) && !file.name.endsWith(".pdf")) {
        toast.error(`${file.name} is not a PDF file`);
        continue;
      }
      if (file.size > MAX_SIZE_BYTES) {
        toast.error(`${file.name} exceeds ${MAX_SIZE_MB} MB limit`);
        continue;
      }
      newItems.push({ file, progress: 0, status: "idle" });
    }
    if (newItems.length > 0) {
      setUploads((prev) => [...prev, ...newItems]);
      // Auto-upload each file
      newItems.forEach((item) => uploadFile(item.file));
    }
  };

  const uploadFile = async (file: File) => {
    setUploads((prev) =>
      prev.map((u) =>
        u.file === file ? { ...u, status: "uploading" as const } : u
      )
    );

    try {
      const response = await uploadApi.upload(
        file,
        title || undefined,
        (progress) => {
          setUploads((prev) =>
            prev.map((u) =>
              u.file === file ? { ...u, progress } : u
            )
          );
        }
      );

      setUploads((prev) =>
        prev.map((u) =>
          u.file === file
            ? { ...u, status: "success" as const, response, progress: 100 }
            : u
        )
      );

      toast.success(`"${response.title}" uploaded successfully`);
      setTitle("");
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : (err as { detail?: string })?.detail ?? "Upload failed";
      setUploads((prev) =>
        prev.map((u) =>
          u.file === file
            ? { ...u, status: "error" as const, error: message }
            : u
        )
      );
      toast.error(message);
    }
  };

  const removeUpload = (file: File) => {
    setUploads((prev) => prev.filter((u) => u.file !== file));
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    addFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(e.target.files);
      e.target.value = "";
    }
  };

  const hasActiveUploads = uploads.some(
    (u) => u.status === "uploading" || u.status === "idle"
  );
  const hasSuccesses = uploads.some((u) => u.status === "success");

  return (
    <div>
      <PageHeader
        title="Upload Papers"
        description="Upload PDF research papers for processing and indexing"
        actions={
          hasSuccesses && !hasActiveUploads ? (
            <Button variant="outline" onClick={() => router.push("/library")}>
              View Library
            </Button>
          ) : undefined
        }
      />

      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Upload PDF files"
        className={cn(
          "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-all duration-300 cursor-pointer",
          "hover:border-primary/50 hover:bg-primary/[0.02]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:border-primary",
          uploads.some((u) => u.status === "uploading") && "pointer-events-none opacity-60"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          aria-hidden="true"
        />

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center"
        >
          <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-primary/10 ring-1 ring-primary/20">
            <Upload className="size-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold">Upload PDF Files</h3>
          <p className="mt-1 mb-4 text-sm text-muted-foreground text-center max-w-sm">
            Drag and drop your PDF files here, or click to browse. Files are
            automatically processed and indexed for search.
          </p>
          <div className="flex items-center gap-2 rounded-lg border bg-muted/50 px-4 py-2 text-sm text-muted-foreground">
            <FileText className="size-4" />
            <span>Supports PDF files up to {MAX_SIZE_MB} MB</span>
          </div>
        </motion.div>
      </div>

      {/* Optional Title */}
      <div className="mt-4 max-w-sm">
        <Label htmlFor="upload-title" className="text-xs text-muted-foreground">
          Optional title for all uploaded files
        </Label>
        <Input
          id="upload-title"
          placeholder="e.g. Attention Is All You Need"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mt-1"
        />
      </div>

      {/* Upload Progress */}
      {uploads.length > 0 && (
        <div className="mt-8">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Brain className="size-4 text-muted-foreground" />
            Uploads ({uploads.length})
          </h3>
          <div className="space-y-2">
            <AnimatePresence>
              {uploads.map((item) => (
                <motion.div
                  key={item.file.name + item.file.size}
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className={cn(
                    "flex items-center justify-between rounded-lg border p-3 transition-colors",
                    item.status === "success" && "border-emerald-500/30 bg-emerald-500/5",
                    item.status === "error" && "border-destructive/30 bg-destructive/5"
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div
                      className={cn(
                        "flex size-8 shrink-0 items-center justify-center rounded-md",
                        item.status === "success" && "bg-emerald-500/10",
                        item.status === "error" && "bg-destructive/10",
                        (item.status === "uploading" || item.status === "idle") && "bg-muted"
                      )}
                    >
                      {item.status === "success" ? (
                        <CheckCircle2 className="size-4 text-emerald-500" />
                      ) : item.status === "error" ? (
                        <AlertCircle className="size-4 text-destructive" />
                      ) : item.status === "uploading" ? (
                        <Loader2 className="size-4 animate-spin text-primary" />
                      ) : (
                        <FileText className="size-4 text-muted-foreground" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {item.file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {(item.file.size / 1024 / 1024).toFixed(1)} MB
                        {item.status === "uploading" && ` · ${item.progress}%`}
                        {item.status === "success" &&
                          ` · Indexed successfully`}
                        {item.status === "error" && ` · ${item.error ?? "Failed"}`}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-4">
                    {/* Progress bar for uploading */}
                    {item.status === "uploading" && (
                      <div className="w-20 h-1.5 rounded-full bg-muted overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${item.progress}%` }}
                          className="h-full rounded-full bg-primary"
                        />
                      </div>
                    )}

                    {/* Remove button */}
                    {(item.status === "success" || item.status === "error") && (
                      <button
                        onClick={() => removeUpload(item.file)}
                        className="flex size-6 items-center justify-center rounded-md text-muted-foreground/50 hover:text-foreground hover:bg-muted transition-colors"
                        aria-label={`Remove ${item.file.name}`}
                      >
                        <X className="size-3.5" />
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  );
}
