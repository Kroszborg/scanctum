'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, XCircle, AlertTriangle, Loader2, Play, RefreshCw } from 'lucide-react';

interface ValidationTarget {
  name: string;
  description: string;
  ground_truth_count: number;
  vulnerabilities: Array<{ name: string; type: string; location: string }>;
}

interface ValidationResult {
  target: string;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export default function ValidationPage() {
  const [targets, setTargets] = useState<Record<string, ValidationTarget>>({});
  const [results, setResults] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState('dvwa');
  const [targetUrl, setTargetUrl] = useState('');
  const [error, setError] = useState('');

  const loadTargets = async () => {
    try {
      const res = await fetch('/api/v1/validate/targets');
      const data = await res.json();
      setTargets(data);
    } catch (err) {
      setError('Failed to load validation targets');
    }
  };

  const runValidation = async () => {
    if (!targetUrl) {
      setError('Please enter the target URL');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/v1/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: selectedTarget,
          target_url: targetUrl,
          scan_mode: 'full',
        }),
      });

      if (!res.ok) throw new Error('Validation failed');

      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 0.9) return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    if (score >= 0.7) return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    return <XCircle className="h-5 w-5 text-red-600" />;
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Validation Testing</h1>
          <p className="text-muted-foreground">
            Test scanner accuracy against known vulnerable applications
          </p>
        </div>
        <Button onClick={loadTargets} variant="outline" size="icon">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="run" className="space-y-4">
        <TabsList>
          <TabsTrigger value="run">Run Validation</TabsTrigger>
          <TabsTrigger value="targets">Validation Targets</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent value="run" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Select Target</CardTitle>
              <CardDescription>
                Choose a vulnerable application to validate against
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(targets).map(([key, target]) => (
                  <Button
                    key={key}
                    variant={selectedTarget === key ? 'default' : 'outline'}
                    onClick={() => setSelectedTarget(key)}
                    className="h-auto p-4 flex flex-col items-start"
                  >
                    <span className="font-semibold">{target.name}</span>
                    <span className="text-xs text-muted-foreground mt-1">
                      {target.ground_truth_count} known vulns
                    </span>
                  </Button>
                ))}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Target URL</label>
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="http://localhost:8080"
                  className="w-full p-2 border rounded"
                />
                <p className="text-xs text-muted-foreground">
                  Enter the URL where the vulnerable application is running
                </p>
              </div>

              <Button onClick={runValidation} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Running Validation...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Run Validation Scan
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="targets">
          <Card>
            <CardHeader>
              <CardTitle>Available Validation Targets</CardTitle>
              <CardDescription>
                Known vulnerable applications with ground truth data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(targets).map(([key, target]) => (
                <div key={key} className="border rounded p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-lg">{target.name}</h3>
                    <Badge variant="secondary">
                      {target.ground_truth_count} vulnerabilities
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{target.description}</p>
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Known Vulnerabilities:</p>
                    <ul className="text-sm text-muted-foreground list-disc list-inside">
                      {target.vulnerabilities.slice(0, 5).map((v, i) => (
                        <li key={i}>
                          {v.type} - {v.location}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results">
          {results ? (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Validation Results - {results.target}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="text-center p-4 border rounded">
                      <p className="text-sm text-muted-foreground">Precision</p>
                      <p className={`text-2xl font-bold ${getScoreColor(results.precision)}`}>
                        {(results.precision * 100).toFixed(1)}%
                      </p>
                      <div className="flex justify-center mt-2">
                        {getScoreIcon(results.precision)}
                      </div>
                    </div>
                    <div className="text-center p-4 border rounded">
                      <p className="text-sm text-muted-foreground">Recall</p>
                      <p className={`text-2xl font-bold ${getScoreColor(results.recall)}`}>
                        {(results.recall * 100).toFixed(1)}%
                      </p>
                      <div className="flex justify-center mt-2">
                        {getScoreIcon(results.recall)}
                      </div>
                    </div>
                    <div className="text-center p-4 border rounded">
                      <p className="text-sm text-muted-foreground">F1 Score</p>
                      <p className={`text-2xl font-bold ${getScoreColor(results.f1_score)}`}>
                        {(results.f1_score * 100).toFixed(1)}%
                      </p>
                      <div className="flex justify-center mt-2">
                        {getScoreIcon(results.f1_score)}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-green-50 rounded">
                      <p className="text-sm text-green-800">True Positives</p>
                      <p className="text-2xl font-bold text-green-600">{results.true_positives}</p>
                    </div>
                    <div className="p-4 bg-red-50 rounded">
                      <p className="text-sm text-red-800">False Positives</p>
                      <p className="text-2xl font-bold text-red-600">{results.false_positives}</p>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded">
                      <p className="text-sm text-yellow-800">False Negatives</p>
                      <p className="text-2xl font-bold text-yellow-600">{results.false_negatives}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                Run a validation scan to see results
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
