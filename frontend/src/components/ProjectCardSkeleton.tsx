import { Card, CardContent, CardHeader } from "./ui/card";

export default function ProjectCardSkeleton() {
  return (
    <Card className="border border-gray-200 animate-pulse">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2 flex-1">
            <div className="w-5 h-5 bg-gray-200 rounded" />
            <div className="h-5 bg-gray-200 rounded w-32" />
          </div>
          <div className="h-6 w-16 bg-gray-200 rounded-full" />
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-24" />
          <div className="h-4 bg-gray-200 rounded w-32" />
          <div className="flex items-center justify-between">
            <div className="h-3 bg-gray-200 rounded w-28" />
            <div className="h-3 bg-gray-200 rounded w-28" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

