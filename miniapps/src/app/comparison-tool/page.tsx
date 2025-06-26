'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { LogOut, Scale, Home, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react'

interface Choice {
  id: string
  name: string
}

interface Criteria {
  id: string
  name: string
}

interface MatrixData {
  [key: string]: {
    grade: number
    notes: string
  }
}

const sampleNotes = [
  "Excellent performance in this area",
  "Good but could be better",
  "Average performance",
  "Below average",
  "Outstanding quality",
  "Meets expectations",
  "Exceeds expectations",
  "Needs improvement",
  "Top tier option",
  "Competitive choice"
]

export default function ComparisonToolPage() {
  const { isAuthenticated, logout } = useAuthStore()
  const router = useRouter()

  // State management
  const [choices, setChoices] = useState<Choice[]>([])
  const [criteria, setCriteria] = useState<Criteria[]>([])
  const [matrixData, setMatrixData] = useState<MatrixData>({})
  const [pivotView, setPivotView] = useState(false)
  const [scoresPivotView, setScoresPivotView] = useState(false)
  const [notesPivotView, setNotesPivotView] = useState(false)
  
  // Collapsible sections state
  const [sectionsOpen, setSectionsOpen] = useState({
    decisionMatrix: true,
    scoresMatrix: true,
    rankings: true,
    detailedNotes: true
  })

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, router])

  // Initialize with sample data
  useEffect(() => {
    if (choices.length === 0 && criteria.length === 0) {
      const sampleChoices = [
        { id: '1', name: 'Tesla Model S' },
        { id: '2', name: 'BMW i4' },
        { id: '3', name: 'Mercedes EQS' }
      ]
      const sampleCriteria = [
        { id: '1', name: 'Price' },
        { id: '2', name: 'Range' },
        { id: '3', name: 'Performance' }
      ]
      
      setChoices(sampleChoices)
      setCriteria(sampleCriteria)
      
      // Generate random data
      const randomData: MatrixData = {}
      sampleChoices.forEach(choice => {
        sampleCriteria.forEach(criteriaItem => {
          const key = `${choice.id}_${criteriaItem.id}`
          randomData[key] = {
            grade: Math.floor(Math.random() * 10) + 1,
            notes: sampleNotes[Math.floor(Math.random() * sampleNotes.length)]
          }
        })
      })
      setMatrixData(randomData)
    }
  }, [choices.length, criteria.length])

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  const updateMatrixData = (choiceId: string, criteriaId: string, field: 'grade' | 'notes', value: string | number) => {
    const key = `${choiceId}_${criteriaId}`
    setMatrixData(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: value
      }
    }))
  }

  const addChoice = () => {
    const newChoice = {
      id: Date.now().toString(),
      name: `Choice ${choices.length + 1}`
    }
    setChoices(prev => [...prev, newChoice])
    
    // Initialize matrix data for new choice
    const newData: MatrixData = {}
    criteria.forEach(criteriaItem => {
      const key = `${newChoice.id}_${criteriaItem.id}`
      newData[key] = { grade: 5, notes: '' }
    })
    setMatrixData(prev => ({ ...prev, ...newData }))
  }

  const addCriteria = () => {
    const newCriteria = {
      id: Date.now().toString(),
      name: `Criteria ${criteria.length + 1}`
    }
    setCriteria(prev => [...prev, newCriteria])
    
    // Initialize matrix data for new criteria
    const newData: MatrixData = {}
    choices.forEach(choice => {
      const key = `${choice.id}_${newCriteria.id}`
      newData[key] = { grade: 5, notes: '' }
    })
    setMatrixData(prev => ({ ...prev, ...newData }))
  }

  const moveChoice = (index: number, direction: 'up' | 'down') => {
    if (direction === 'up' && index > 0) {
      setChoices(prev => {
        const newChoices: Choice[] = [...prev]
        const temp = newChoices[index]
        newChoices[index] = newChoices[index - 1]
        newChoices[index - 1] = temp
        return newChoices
      })
    } else if (direction === 'down' && index < choices.length - 1) {
      setChoices(prev => {
        const newChoices: Choice[] = [...prev]
        const temp = newChoices[index]
        newChoices[index] = newChoices[index + 1]
        newChoices[index + 1] = temp
        return newChoices
      })
    }
  }

  const deleteChoice = (choiceId: string) => {
    setChoices(prev => prev.filter(choice => choice.id !== choiceId))
    // Remove matrix data for deleted choice
    const newData = { ...matrixData }
    criteria.forEach(criteriaItem => {
      delete newData[`${choiceId}_${criteriaItem.id}`]
    })
    setMatrixData(newData)
  }

  const deleteCriteria = (criteriaId: string) => {
    setCriteria(prev => prev.filter(criteriaItem => criteriaItem.id !== criteriaId))
    // Remove matrix data for deleted criteria
    const newData = { ...matrixData }
    choices.forEach(choice => {
      delete newData[`${choice.id}_${criteriaId}`]
    })
    setMatrixData(newData)
  }

  const loadTestData = () => {
    const testChoices = [
      { id: '1', name: 'Tesla Model S' },
      { id: '2', name: 'BMW i4' },
      { id: '3', name: 'Mercedes EQS' },
      { id: '4', name: 'Audi e-tron' },
      { id: '5', name: 'Porsche Taycan' }
    ]
    const testCriteria = [
      { id: '1', name: 'Price' },
      { id: '2', name: 'Range' },
      { id: '3', name: 'Performance' },
      { id: '4', name: 'Charging Speed' },
      { id: '5', name: 'Interior Quality' }
    ]
    
    setChoices(testChoices)
    setCriteria(testCriteria)
    
    // Generate random data
    const randomData: MatrixData = {}
    testChoices.forEach(choice => {
      testCriteria.forEach(criteriaItem => {
        const key = `${choice.id}_${criteriaItem.id}`
        randomData[key] = {
          grade: Math.floor(Math.random() * 10) + 1,
          notes: sampleNotes[Math.floor(Math.random() * sampleNotes.length)]
        }
      })
    })
    setMatrixData(randomData)
  }

  const calculateScores = () => {
    const scores = choices.map(choice => {
      let totalScore = 0
      const criteriaScores: { [key: string]: number } = {}
      
      criteria.forEach(criteriaItem => {
        const key = `${choice.id}_${criteriaItem.id}`
        const grade = matrixData[key]?.grade || 0
        criteriaScores[criteriaItem.name] = grade
        totalScore += grade
      })
      
      return {
        choice: choice.name,
        totalScore,
        averageScore: Math.round((totalScore / criteria.length) * 100) / 100,
        criteriaScores
      }
    })
    
    return scores.sort((a, b) => b.totalScore - a.totalScore)
  }

  const toggleSection = (section: keyof typeof sectionsOpen) => {
    setSectionsOpen(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  if (!isAuthenticated) {
    return null
  }

  const scores = calculateScores()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Scale className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Decision Matrix Comparator</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/home')}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                <Home className="h-4 w-4 mr-2" />
                Home
              </button>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Sidebar */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">📝 Input Data</h2>
                
                <button
                  onClick={loadTestData}
                  className="w-full mb-4 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  📊 Load Test Data
                </button>

                {/* Choices */}
                <div className="mb-6">
                  <h3 className="font-medium mb-2">Choices</h3>
                  <div className="space-y-2">
                    {choices.map((choice, index) => (
                      <div key={choice.id} className="flex items-center space-x-2">
                        <span className="flex-1 text-sm">• {choice.name}</span>
                        <button
                          onClick={() => moveChoice(index, 'up')}
                          disabled={index === 0}
                          className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
                        >
                          ⬆️
                        </button>
                        <button
                          onClick={() => moveChoice(index, 'down')}
                          disabled={index === choices.length - 1}
                          className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
                        >
                          ⬇️
                        </button>
                        <button
                          onClick={() => deleteChoice(choice.id)}
                          className="text-red-400 hover:text-red-600"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={addChoice}
                    className="mt-2 w-full bg-green-600 text-white py-1 px-3 rounded text-sm hover:bg-green-700"
                  >
                    + Add Choice
                  </button>
                </div>

                {/* Criteria */}
                <div className="mb-6">
                  <h3 className="font-medium mb-2">Criteria</h3>
                  <div className="space-y-2">
                    {criteria.map((criteriaItem, index) => (
                      <div key={criteriaItem.id} className="flex items-center space-x-2">
                        <span className="flex-1 text-sm">• {criteriaItem.name}</span>
                        <button
                          onClick={() => deleteCriteria(criteriaItem.id)}
                          className="text-red-400 hover:text-red-600"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={addCriteria}
                    className="mt-2 w-full bg-green-600 text-white py-1 px-3 rounded text-sm hover:bg-green-700"
                  >
                    + Add Criteria
                  </button>
                </div>

                {/* Pivot Controls */}
                <div className="space-y-2">
                  <button
                    onClick={() => setPivotView(!pivotView)}
                    className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                  >
                    <RotateCcw className="h-4 w-4 inline mr-2" />
                    {pivotView ? 'Normal View' : 'Pivot View'}
                  </button>
                </div>
              </div>
            </div>

            {/* Main Content Area */}
            <div className="lg:col-span-3 space-y-6">
              {/* Decision Matrix Section */}
              <div className="bg-white rounded-lg shadow">
                <button
                  onClick={() => toggleSection('decisionMatrix')}
                  className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50"
                >
                  <h2 className="text-lg font-semibold">📊 Decision Matrix</h2>
                  {sectionsOpen.decisionMatrix ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                </button>
                
                {sectionsOpen.decisionMatrix && (
                  <div className="px-6 pb-6">
                    {pivotView ? (
                      <div className="space-y-4">
                        <h3 className="font-medium">Criteria vs Choices</h3>
                        {criteria.map(criteriaItem => (
                          <div key={criteriaItem.id} className="border rounded-lg p-4">
                            <h4 className="font-medium mb-3">{criteriaItem.name}</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                              {choices.map(choice => {
                                const key = `${choice.id}_${criteriaItem.id}`
                                const data = matrixData[key] || { grade: 5, notes: '' }
                                return (
                                  <div key={choice.id} className="border rounded p-3">
                                    <h5 className="font-medium text-sm mb-2">{choice.name}</h5>
                                    <div className="flex items-center space-x-2 mb-2">
                                      <input
                                        type="number"
                                        min="1"
                                        max="10"
                                        value={data.grade}
                                        onChange={(e) => updateMatrixData(choice.id, criteriaItem.id, 'grade', parseInt(e.target.value))}
                                        className="w-16 px-2 py-1 border rounded text-sm"
                                      />
                                      <span className="text-sm text-gray-600">Grade</span>
                                    </div>
                                    <textarea
                                      value={data.notes}
                                      onChange={(e) => updateMatrixData(choice.id, criteriaItem.id, 'notes', e.target.value)}
                                      placeholder="Notes..."
                                      className="w-full px-2 py-1 border rounded text-sm resize-none"
                                      rows={3}
                                    />
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <h3 className="font-medium">Choices vs Criteria</h3>
                        {choices.map(choice => (
                          <div key={choice.id} className="border rounded-lg p-4">
                            <h4 className="font-medium mb-3">{choice.name}</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                              {criteria.map(criteriaItem => {
                                const key = `${choice.id}_${criteriaItem.id}`
                                const data = matrixData[key] || { grade: 5, notes: '' }
                                return (
                                  <div key={criteriaItem.id} className="border rounded p-3">
                                    <h5 className="font-medium text-sm mb-2">{criteriaItem.name}</h5>
                                    <div className="flex items-center space-x-2 mb-2">
                                      <input
                                        type="number"
                                        min="1"
                                        max="10"
                                        value={data.grade}
                                        onChange={(e) => updateMatrixData(choice.id, criteriaItem.id, 'grade', parseInt(e.target.value))}
                                        className="w-16 px-2 py-1 border rounded text-sm"
                                      />
                                      <span className="text-sm text-gray-600">Grade</span>
                                    </div>
                                    <textarea
                                      value={data.notes}
                                      onChange={(e) => updateMatrixData(choice.id, criteriaItem.id, 'notes', e.target.value)}
                                      placeholder="Notes..."
                                      className="w-full px-2 py-1 border rounded text-sm resize-none"
                                      rows={3}
                                    />
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Scores Matrix Section */}
              <div className="bg-white rounded-lg shadow">
                <button
                  onClick={() => toggleSection('scoresMatrix')}
                  className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-4">
                    <h2 className="text-lg font-semibold">📊 Scores Matrix</h2>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setScoresPivotView(!scoresPivotView)
                      }}
                      className="bg-purple-600 text-white px-2 py-1 rounded text-xs hover:bg-purple-700"
                    >
                      <RotateCcw className="h-3 w-3 inline mr-1" />
                      {scoresPivotView ? 'Normal' : 'Pivot'}
                    </button>
                  </div>
                  {sectionsOpen.scoresMatrix ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                </button>
                
                {sectionsOpen.scoresMatrix && (
                  <div className="px-6 pb-6">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            {scoresPivotView ? (
                              <>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Criteria
                                </th>
                                {choices.map(choice => (
                                  <th key={choice.id} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    {choice.name}
                                  </th>
                                ))}
                              </>
                            ) : (
                              <>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Choice
                                </th>
                                {criteria.map(criteriaItem => (
                                  <th key={criteriaItem.id} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    {criteriaItem.name}
                                  </th>
                                ))}
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Total Score
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Average
                                </th>
                              </>
                            )}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {scoresPivotView ? (
                            criteria.map(criteriaItem => (
                              <tr key={criteriaItem.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {criteriaItem.name}
                                </td>
                                {choices.map(choice => {
                                  const key = `${choice.id}_${criteriaItem.id}`
                                  const grade = matrixData[key]?.grade || 0
                                  return (
                                    <td key={choice.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                      {grade}
                                    </td>
                                  )
                                })}
                              </tr>
                            ))
                          ) : (
                            scores.map((score, index) => (
                              <tr key={index}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {score.choice}
                                </td>
                                {criteria.map(criteriaItem => (
                                  <td key={criteriaItem.id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {score.criteriaScores[criteriaItem.name]}
                                  </td>
                                ))}
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {score.totalScore}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  {score.averageScore}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              {/* Rankings Section */}
              <div className="bg-white rounded-lg shadow">
                <button
                  onClick={() => toggleSection('rankings')}
                  className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50"
                >
                  <h2 className="text-lg font-semibold">🏆 Rankings</h2>
                  {sectionsOpen.rankings ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                </button>
                
                {sectionsOpen.rankings && (
                  <div className="px-6 pb-6">
                    <div className="space-y-3">
                      {scores.map((score, index) => {
                        const medal = index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : "📊"
                        return (
                          <div key={index} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
                            <span className="text-2xl">{medal}</span>
                            <div className="flex-1">
                              <span className="font-medium">{score.choice}</span>
                            </div>
                            <div className="text-right">
                              <div className="font-medium">{score.totalScore} pts</div>
                              <div className="text-sm text-gray-600">avg: {score.averageScore}</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Detailed Notes Section */}
              <div className="bg-white rounded-lg shadow">
                <button
                  onClick={() => toggleSection('detailedNotes')}
                  className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-4">
                    <h2 className="text-lg font-semibold">📝 Detailed Notes</h2>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setNotesPivotView(!notesPivotView)
                      }}
                      className="bg-purple-600 text-white px-2 py-1 rounded text-xs hover:bg-purple-700"
                    >
                      <RotateCcw className="h-3 w-3 inline mr-1" />
                      {notesPivotView ? 'Normal' : 'Pivot'}
                    </button>
                  </div>
                  {sectionsOpen.detailedNotes ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                </button>
                
                {sectionsOpen.detailedNotes && (
                  <div className="px-6 pb-6">
                    {notesPivotView ? (
                      <div className="space-y-4">
                        {criteria.map(criteriaItem => (
                          <details key={criteriaItem.id} className="border rounded-lg">
                            <summary className="px-4 py-3 cursor-pointer font-medium text-gray-900 hover:bg-gray-50">
                              Notes for {criteriaItem.name}
                            </summary>
                            <div className="px-4 pb-4 space-y-2">
                              {choices.map(choice => {
                                const key = `${choice.id}_${criteriaItem.id}`
                                const notes = matrixData[key]?.notes
                                return notes ? (
                                  <div key={choice.id} className="text-sm">
                                    <span className="font-medium">{choice.name}:</span> {notes}
                                  </div>
                                ) : null
                              })}
                            </div>
                          </details>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {choices.map(choice => (
                          <details key={choice.id} className="border rounded-lg">
                            <summary className="px-4 py-3 cursor-pointer font-medium text-gray-900 hover:bg-gray-50">
                              Notes for {choice.name}
                            </summary>
                            <div className="px-4 pb-4 space-y-2">
                              {criteria.map(criteriaItem => {
                                const key = `${choice.id}_${criteriaItem.id}`
                                const notes = matrixData[key]?.notes
                                return notes ? (
                                  <div key={criteriaItem.id} className="text-sm">
                                    <span className="font-medium">{criteriaItem.name}:</span> {notes}
                                  </div>
                                ) : null
                              })}
                            </div>
                          </details>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 