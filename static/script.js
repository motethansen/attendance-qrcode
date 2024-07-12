document.addEventListener("DOMContentLoaded", function() {
    console.log("JavaScript loaded from static/script.js");
    
    let attendanceChart = null;

    function updateQRCode() {
        fetch('/get_qr_url')
            .then(response => response.json())
            .then(data => {
                document.getElementById('qr-code').src = data.url + '?t=' + new Date().getTime();
                startCountdown();
            });
    }

    function startCountdown() {
        let seconds = 15;
        const timerElement = document.getElementById('seconds');
        
        const countdownInterval = setInterval(() => {
            seconds--;
            timerElement.textContent = seconds;
            
            if (seconds <= 0) {
                clearInterval(countdownInterval);
                updateQRCode();
                updateScanCount();
                // updateAttendanceList();
                //updateAttendanceChart();
            }
        }, 1000);
    }

    function updateScanCount() {
        fetch('/get_scan_count')
            .then(response => response.json())
            .then(data => {
                document.getElementById('scan-count').textContent = data.count;
                document.getElementById('acount').textContent = data.acount;
                //updateAttendanceChart(); // Ensure the chart updates when the count changes
            });
    }

    function updateAttendanceChart() {
        fetch('/get_total_students')
            .then(response => response.json())
            .then(data => {
                const totalStudents = data.total_students;
                const attendanceCount = data.attendancecount;//parseInt(document.getElementById('acount').textContent, 10);
                const notAttendedCount = totalStudents - attendanceCount;

                if (isNaN(attendanceCount) || isNaN(notAttendedCount)) {
                    console.error('Invalid data for chart:', { attendanceCount, notAttendedCount });
                    return;
                }

                const ctx = document.getElementById('attendanceChart').getContext('2d');

                 // Destroy the previous chart instance if it exists
                if (attendanceChart) {
                    attendanceChart.destroy();
                }

                attendanceChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: ['Attended', 'Not Attended'],
                        datasets: [{
                            data: [attendanceCount, notAttendedCount],
                            backgroundColor: ['#36a2eb', '#ff6384']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            datalabels: {
                                color: '#fff',
                                font: {
                                    size: 18,
                                    weight: 'bold'
                                },
                                formatter: (value) => value
                                // formatter: (value, context) => {
                                //     let dataset = context.chart.data.datasets[0];
                                //     let total = dataset.data.reduce((prev, curr) => prev + curr, 0);
                                //     let percentage = Math.round((value / total) * 100);
                                //     return percentage + '%';
                                // }
                            }
                        }
                    },
                    plugins: [ChartDataLabels]
                });
            })
            .catch(error => console.error('Error updating chart:', error));
    }

    updateQRCode();
    setInterval(updateScanCount, 5000); // Update scan count every 5 seconds
    setInterval(updateAttendanceChart, 15000); // Update attendance chart every 5 seconds
});