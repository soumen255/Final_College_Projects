                
                if status == "Pass":
                    semester_credits += credits
                    semester_grade_points += credits * grade_point
                    total_credits_all += credits
                    total_grade_points_all += credits * grade_point
            
            # Calculate semester SGPA
            if semester_credits > 0:
                sgpa = semester_grade_points / semester_credits
                
                sgpa_frame = ttk.Frame(semester_frame)
                sgpa_frame.pack(fill=tk.X, pady=5)
                
                ttk.Label(sgpa_frame, text=f"Semester {semester} SGPA: {sgpa:.2f}", 
                         font=('Arial', 12, 'bold'), foreground="blue").pack()
        
        # Update overall statistics
        if total_credits_all > 0:
            cgpa = total_grade_points_all / total_credits_all
            self.cgpa_label.config(text=f"{cgpa:.2f}")
            self.total_credits_label.config(text=str(total_credits_all))
        else:
            self.cgpa_label.config(text="0.00")
            self.total_credits_label.config(text="0")
        
        self.current_semester_label.config(text=str(current_semester))
        
        if not semesters_with_data:
            messagebox.showinfo("Info", "No grade data found for the selected student!")

def main():
    root = tk.Tk()
    app = ProfessionalCollegeGradeSystem(root)
    root.mainloop() 

if __name__ == "__main__":
    main()