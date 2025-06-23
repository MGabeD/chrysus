import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUser } from "@/contexts/UserContext";
import { toast } from "@/hooks/use-toast";
import { buildApiUrl } from "@/lib/config";

export const PdfUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setUsers } = useUser();

  const uploadFile = async (file: File) => {
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(buildApiUrl("upload_pdf/"), {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        toast({
          title: "Upload successful",
          description: `${file.name} has been processed successfully.`,
        });

        // Refresh users list after successful upload
        const usersResponse = await fetch(buildApiUrl("users"));
        if (usersResponse.ok) {
          const data = await usersResponse.json();
          setUsers(data.users.map((name: string) => ({ name })));
        }
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "There was an error processing your file.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (file: File) => {
    if (file.type === "application/pdf") {
      uploadFile(file);
    } else {
      toast({
        title: "Invalid file type",
        description: "Please select a PDF file.",
        variant: "destructive",
      });
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Upload PDF</h2>

      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragOver
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <div className="space-y-3">
          {uploading ? (
            <div className="animate-spin mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          ) : (
            <Upload className="mx-auto w-8 h-8 text-gray-400" />
          )}

          <div>
            <p className="text-sm font-medium text-gray-900">
              {uploading ? "Processing..." : "Drop PDF here or click to upload"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Bank statements in PDF format
            </p>
          </div>

          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            variant="outline"
            size="sm"
          >
            <FileText className="w-4 h-4 mr-2" />
            Select File
          </Button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileSelect(file);
            }}
          />
        </div>
      </div>
    </div>
  );
};
